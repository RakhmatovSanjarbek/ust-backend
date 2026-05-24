import re
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from collections import defaultdict

from accounts.models import User
from .models import Cargo, WarehouseCargo, OnWayCargo, ArrivedCargo, DeliveredCargo
from utils.push_service import send_flight_status_push, send_cargo_status_push


# --- Transport turini aniqlash ---
def get_transport_type_from_id(id_value):
    if not id_value:
        return None
    clean = re.sub(r'[\s\-]', '', str(id_value).strip().upper())
    if clean.startswith('US') and re.match(r'^US\d', clean):
        return 'AVIA'
    elif clean.startswith('GG') and re.match(r'^GG\d', clean):
        return 'AVTO'
    return None


def extract_number_from_id(id_value):
    """Raqamni ajratib oladi: A-0102 → 102, UT-0102 → 102, UTS 0102 → 102"""
    if not id_value:
        return None
    id_str = str(id_value).strip()
    match = re.search(r'(\d+)', id_str)
    if match:
        # Oldidagi nollarni olib tashlaymiz: 0102 → 102
        return str(int(match.group(1)))
    return None


# --- Resource ---
class CargoResource(resources.ModelResource):
    track_code = Field(attribute='track_code', column_name='TREK RAQAM')
    flight_name = Field(attribute='flight_name', column_name='REYS')
    id_field = Field(attribute='user', column_name='ID')
    created_at = Field(attribute='created_at', column_name='OMBORDA')

    class Meta:
        model = Cargo
        import_id_fields = ()
        fields = ('track_code', 'flight_name', 'created_at', 'status', 'user')
        skip_unchanged = True
        report_skipped = True
        export_order = ('track_code', 'flight_name', 'created_at', 'status', 'user')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_cache = {}
        self._pending_cargos = []
        self._imported_count = 0
        self._pending_count = 0
        # ✅ Import natijasida saqlangan yuk ID-larini yig'amiz (push uchun)
        self._new_cargo_ids = []
        self.request = None

    def get_import_id_fields(self):
        return []

    def _find_user_by_number(self, number):
        """
        Raqam bo'yicha foydalanuvchini topadi.
        Barcha formatlarni qoplaydi:
          102   → UTS-0102, UTS-102, UTS0102, UT-0102, A-0102, A-102 ...
          0102  → UTS-0102, UTS0102, UT-0102, A-0102 ...
        """
        if not number:
            return None
        if number in self._user_cache:
            return self._user_cache[number]

        # Raqamni normalize qilamiz: "0102" va "102" ikkalasini ham sinab ko'ramiz
        num = str(int(number))        # "0102" → "102"
        num_padded = num.zfill(4)     # "102"  → "0102"

        patterns = []
        for n in [num, num_padded]:
            patterns.extend([
                f"US-{n}", f"US{n}", f"US {n}",
                f"GG-{n}", f"GG{n}", f"GG {n}",
            ])

        # Duplikatlarni olib tashlaymiz (num == num_padded bo'lishi mumkin)
        patterns = list(dict.fromkeys(patterns))

        user = None
        for pattern in patterns:
            user = User.objects.filter(user_id__iexact=pattern).first()
            if user:
                break

        # Hali ham topilmasa — raqam bo'yicha qidirish
        if not user:
            user = User.objects.filter(user_id__icontains=num).first()

        self._user_cache[number] = user
        return user

    def before_import(self, dataset, **kwargs):
        self._user_cache = {}
        self._pending_cargos = []
        self._imported_count = 0
        self._pending_count = 0
        self._new_cargo_ids = []

        rows_to_remove = []
        for i, row in enumerate(dataset.dict):
            if all(not str(v).strip() or str(v).strip().lower() in ['none', 'null', ''] for v in row.values()):
                rows_to_remove.append(i)
        for i in reversed(rows_to_remove):
            del dataset[i]

    def before_import_row(self, row, **kwargs):
        try:
            track_code = row.get('TREK RAQAM', '')
            if track_code:
                track_code = str(track_code).strip()

            if not track_code or track_code.lower() in ['none', 'null', '']:
                return False

            flight_name = row.get('REYS', 'R-125')
            flight_name = str(flight_name).strip() if flight_name else 'R-125'

            id_value = row.get('ID', '')
            if id_value:
                id_value = str(id_value).strip()

            number = extract_number_from_id(id_value)
            transport_type = get_transport_type_from_id(id_value)

            user = self._find_user_by_number(number) if number else None

            created_at = row.get('OMBORDA', '')
            if not created_at or str(created_at).strip() in ['', 'None', 'null']:
                created_at = timezone.now()

            row['track_code'] = track_code
            row['flight_name'] = flight_name
            row['created_at'] = created_at

            if user:
                row['user'] = user.pk
                row['status'] = 'Omborda'
                self._imported_count += 1
            else:
                row['user'] = None
                row['status'] = 'Kutilmoqda'
                self._pending_count += 1
                self._pending_cargos.append({
                    'track_code': track_code,
                    'id_value': id_value,
                    'number': number,
                    'transport_type': transport_type,
                })
            return True
        except Exception as e:
            print(f"Qatorni qayta ishlashda xatolik: {e}")
            return False

    def skip_row(self, instance, original, row, import_validation_errors=None):
        return False

    def get_instance(self, instance_loader, row):
        track_code = row.get('track_code')
        if track_code:
            try:
                return self._meta.model.objects.get(track_code=track_code)
            except self._meta.model.DoesNotExist:
                return None
        return None

    def before_save_instance(self, instance, row, **kwargs):
        """
        ✅ ASOSIY TUZATISH: Import paytida post_save signalni o'chiramiz.
        Push import tugagandan keyin after_import da BIR MARTA guruhlab yuboriladi.
        """
        instance._skip_push_signal = True

        if self.request and instance.user:
            if not instance.pk:
                instance.created_by = self.request.user
                instance.warehouse_admin = self.request.user
            instance.updated_by = self.request.user

    def after_import_row(self, row, row_result, **kwargs):
        """
        ✅ TUZATILDI: Push bu yerda YUKLANMAYDI.
        Faqat yangi yuk ID-larini yig'amiz.
        after_import da BIR MARTA guruhlab yuboriladi.
        """
        if row_result.import_type in ['new', 'update']:
            try:
                cargo_id = row_result.object_id
                if cargo_id:
                    self._new_cargo_ids.append(cargo_id)
            except Exception as e:
                print(f"ID yig'ishda xato: {e}")

    def after_import(self, dataset, result, **kwargs):
        """
        ✅ ASOSIY TUZATISH: Barcha import tugagach, REYS BO'YICHA GURUHLAB bitta push.
        Har bir foydalanuvchiga bitta xabar ketadi.
        """
        if self._new_cargo_ids:
            # Foydalanuvchisi bor va "Omborda" statusidagi yangi yuklarni olamiz
            new_cargos = list(
                Cargo.objects.filter(
                    pk__in=self._new_cargo_ids,
                    user__isnull=False,
                    status='Omborda'
                ).select_related('user')
            )

            if new_cargos:
                success, error = send_flight_status_push(new_cargos, 'Omborda')
                print(f"[IMPORT PUSH] ✅ {success} foydalanuvchiga yuborildi | ❌ {error} xato")

        print(f"""
╔══════════════════════════════════════════════════════════╗
║                    IMPORT NATIJALARI                      ║
╠══════════════════════════════════════════════════════════╣
║  ✅ Muvaffaqiyatli import: {self._imported_count} ta yuk
║  ⏳ Kutilayotgan (foydalanuvchi topilmadi): {self._pending_count} ta
╚══════════════════════════════════════════════════════════╝
        """)


# --- Asosiy Admin klassi ---
class BaseCargoAdmin(ImportExportModelAdmin):
    resource_class = CargoResource

    list_display = (
        'track_code', 'display_user_info', 'flight_name',
        'colored_status', 'created_at', 'get_transport_badge', 'get_responsible_admin'
    )
    list_filter = ('status', 'flight_name', 'created_at')
    search_fields = ('track_code', 'user__user_id', 'flight_name')
    readonly_fields = (
        'created_by', 'updated_by', 'warehouse_admin',
        'onway_admin', 'arrived_admin', 'delivered_admin', 'delivered_at'
    )

    def get_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_resource_kwargs(request, *args, **kwargs)
        self.resource_class.request = request
        return kwargs

    def display_user_info(self, obj):
        if obj.user:
            return format_html(
                '<span style="font-weight: bold; background-color: #e8f4fd; padding: 2px 8px; border-radius: 4px;">'
                '👤 {}<br><span style="font-size: 11px; color: #666;">({})</span></span>',
                obj.user.user_id if obj.user.user_id else '-',
                obj.user.get_full_name() or obj.user.phone or '-'
            )
        return format_html(
            '<span style="color: #e74c3c; background-color: #fef5f5; padding: 2px 8px; border-radius: 4px;">'
            '⚠️ Foydalanuvchi topilmadi<br><span style="font-size: 10px;">Kutilmoqda</span></span>'
        )
    display_user_info.short_description = "Foydalanuvchi"

    def get_transport_badge(self, obj):
        if obj.user and obj.user.user_id:
            user_id = obj.user.user_id.upper()
            if 'US' in user_id:
                return format_html('<span style="...">✈️ AVIA</span>')
            elif 'GG' in user_id:
                return format_html('<span style="...">🚚 AVTO</span>')
        return format_html('<span style="...">❓ ANIQLANMAGAN</span>')
    get_transport_badge.short_description = "Transport"

    def colored_status(self, obj):
        colors = {
            'Omborda': '#f39c12',
            "Yo'lda": '#3498db',
            'Punktda': '#9b59b6',
            'Topshirildi': '#27ae60',
            'Kutilmoqda': '#e74c3c'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 11px; display: inline-block;">{}</span>',
            colors.get(obj.status, '#95a5a6'),
            obj.status
        )
    colored_status.short_description = "Holati"

    def get_responsible_admin(self, obj):
        admin_map = {
            'Omborda': obj.warehouse_admin,
            "Yo'lda": obj.onway_admin,
            'Punktda': obj.arrived_admin,
            'Topshirildi': obj.delivered_admin,
            'Kutilmoqda': None
        }
        admin = admin_map.get(obj.status)
        if admin:
            name = admin.get_full_name() or admin.first_name or str(admin.phone) or admin.username
            return format_html('<span style="color: #2c3e50;">👤 {}</span>', name[:30])
        elif obj.status == 'Kutilmoqda':
            return format_html('<span style="color: #e74c3c;">⏳ Foydalanuvchi kutilmoqda</span>')
        return format_html('<span style="color: #bdc3c7;">⚪ Belgilanmagan</span>')
    get_responsible_admin.short_description = "Mas'ul Admin"

    def save_model(self, request, obj, form, change):
        """
        Yakka tartibda tahrirlab saqlaganda.
        ✅ Signal avtomatik push yuboradi — bu yerda qo'shimcha push KERAK EMAS.
        """
        if not change and obj.user:
            obj.created_by = request.user

        if obj.user:
            if 'status' in form.changed_data or not change:
                if obj.status == 'Omborda':
                    obj.warehouse_admin = request.user
                elif obj.status == "Yo'lda":
                    obj.onway_admin = request.user
                elif obj.status == 'Punktda':
                    obj.arrived_admin = request.user
                elif obj.status == 'Topshirildi':
                    obj.delivered_admin = request.user
                    obj.delivered_at = timezone.now()
            obj.updated_by = request.user
        else:
            obj.status = 'Kutilmoqda'

        # ✅ Signal ishlashi uchun _skip_push_signal = False (default)
        obj._skip_push_signal = False
        super().save_model(request, obj, form, change)


# --- Modellarni registratsiya qilish ---
@admin.register(Cargo)
class AllCargoAdmin(BaseCargoAdmin):
    """Barcha yuklar"""
    pass


@admin.register(WarehouseCargo)
class WarehouseCargoAdmin(BaseCargoAdmin):
    """Ombordagi yuklar"""
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Omborda')

    actions = ['make_onway']

    @admin.action(description="🚚 Yo'lga chiqarish")
    def make_onway(self, request, queryset):
        cargo_ids = list(queryset.values_list('pk', flat=True))

        # ✅ Bulk update — signal ishlamaydi, shuning uchun push qo'lda
        queryset.update(
            status="Yo'lda",
            onway_admin=request.user,
            updated_by=request.user
        )

        # ✅ Reys bo'yicha GURUHLAB push yuboramiz
        updated_cargos = list(Cargo.objects.filter(pk__in=cargo_ids).select_related('user'))
        success, error = send_flight_status_push(updated_cargos, "Yo'lda")

        self.message_user(
            request,
            f"{len(cargo_ids)} ta yuk yo'lga chiqarildi. "
            f"✅ {success} foydalanuvchiga push yuborildi. ❌ {error} xato."
        )


@admin.register(OnWayCargo)
class OnWayCargoAdmin(BaseCargoAdmin):
    """Yo'ldagi yuklar"""
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status="Yo'lda")

    actions = ['make_arrived']

    @admin.action(description="📍 Punktga yetkazish")
    def make_arrived(self, request, queryset):
        cargo_ids = list(queryset.values_list('pk', flat=True))

        queryset.update(
            status='Punktda',
            arrived_admin=request.user,
            updated_by=request.user
        )

        updated_cargos = list(Cargo.objects.filter(pk__in=cargo_ids).select_related('user'))
        success, error = send_flight_status_push(updated_cargos, 'Punktda')

        self.message_user(
            request,
            f"{len(cargo_ids)} ta yuk punktga yetkazildi. "
            f"✅ {success} foydalanuvchiga bildirishnoma yuborildi. ❌ {error} xato."
        )


@admin.register(ArrivedCargo)
class ArrivedCargoAdmin(BaseCargoAdmin):
    """Punktdagi yuklar"""
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Punktda')

    actions = ['make_delivered']

    @admin.action(description="✅ Topshirildi")
    def make_delivered(self, request, queryset):
        cargo_ids = list(queryset.values_list('pk', flat=True))

        queryset.update(
            status='Topshirildi',
            delivered_admin=request.user,
            delivered_at=timezone.now(),
            updated_by=request.user
        )

        updated_cargos = list(Cargo.objects.filter(pk__in=cargo_ids).select_related('user'))
        success, error = send_flight_status_push(updated_cargos, 'Topshirildi')

        self.message_user(
            request,
            f"{len(cargo_ids)} ta yuk topshirildi. "
            f"✅ {success} foydalanuvchiga push yuborildi. ❌ {error} xato."
        )


@admin.register(DeliveredCargo)
class DeliveredCargoAdmin(BaseCargoAdmin):
    """Topshirilgan yuklar"""
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Topshirildi')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False