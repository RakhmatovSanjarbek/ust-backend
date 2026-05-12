import re
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field

from accounts.models import User
from .models import Cargo, WarehouseCargo, OnWayCargo, ArrivedCargo, DeliveredCargo


# --- Transport turini aniqlash ---
def get_transport_type_from_id(id_value):
    """
    ID dan transport turini aniqlaydi
    UT-0102 -> Avia
    A-0102 -> Avto
    """
    if not id_value:
        return None

    trek_str = str(id_value).strip().upper()

    # Agar trek raqamda A yoki UT bo'lsa
    if 'A' in trek_str or trek_str.startswith('A'):
        return 'AVIA'
    elif 'UT' in trek_str or trek_str.startswith('UT'):
        return 'AVTO'
    else:
        return None


def extract_number_from_id(id_value):
    """
    ID dan faqat raqamli qismni ajratib oladi
    UT-0102 -> 0102
    A-0102 -> 0102
    UTS-0102 -> 0102
    """
    if not id_value:
        return None

    id_str = str(id_value).strip()
    # Faqat raqamlarni topish
    match = re.search(r'(\d+)', id_str)
    if match:
        return match.group(1)
    return None


# --- Optimallashtirilgan Resource ---
class CargoResource(resources.ModelResource):
    # Import qilishda ishlatiladigan maydonlar
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
        self._pending_cargos = []  # Foydalanuvchisi topilmagan yuklar
        self._imported_count = 0
        self._pending_count = 0
        self.request = None

    def get_import_id_fields(self):
        return []

    def _find_user_by_number(self, number):
        """
        Raqam bo'yicha foydalanuvchini topadi
        Misol: 0102 raqami bilan UTS-0102, UTS0102, UT-0102, A-0102 formatlarini qidiradi
        """
        if not number:
            return None

        # Cache'dan tekshirish
        if number in self._user_cache:
            return self._user_cache[number]

        user = None

        # Turli formatlarda qidirish
        patterns = [
            f"UTS-{number}",
            f"UTS{number}",
            f"UTS {number}",
            f"UT-{number}",
            f"UT{number}",
            f"A-{number}",
            f"A{number}",
        ]

        # 3 xonali raqam bo'lsa, 4 xonali formatda ham qidirish
        if len(number) == 3:
            patterns.extend([
                f"UTS-0{number}",
                f"UTS0{number}",
                f"UT-0{number}",
                f"A-0{number}",
            ])

        for pattern in patterns:
            user = User.objects.filter(user_id__iexact=pattern).first()
            if user:
                break

        # Agar topilmasa, raqamni o'z ichiga olganlarni qidirish
        if not user:
            user = User.objects.filter(user_id__icontains=number).first()

        # Cache'ga saqlash
        self._user_cache[number] = user
        return user

    def before_import(self, dataset, **kwargs):
        """Import boshlanishida statistikani tozalash"""
        self._user_cache = {}
        self._pending_cargos = []
        self._imported_count = 0
        self._pending_count = 0

        # Datasetni tozalash - bo'sh qatorlarni olib tashlash
        rows_to_remove = []
        for i, row in enumerate(dataset.dict):
            if all(not str(v).strip() or str(v).strip().lower() in ['none', 'null', ''] for v in row.values()):
                rows_to_remove.append(i)

        for i in reversed(rows_to_remove):
            del dataset[i]

    def before_import_row(self, row, **kwargs):
        """
        Har bir qatorni import qilishdan oldin ishlov berish
        """
        try:
            # Trek kodni olish
            track_code = row.get('TREK RAQAM', '')
            if track_code:
                track_code = str(track_code).strip()

            # Agar trek kod bo'sh bo'lsa, qatorni o'tkazib yuborish
            if not track_code or track_code.lower() in ['none', 'null', '']:
                return False

            # Reys nomi
            flight_name = row.get('REYS', 'R-125')
            if flight_name:
                flight_name = str(flight_name).strip()
            else:
                flight_name = 'R-125'

            # ID (UT-0102 yoki A-0102)
            id_value = row.get('ID', '')
            if id_value:
                id_value = str(id_value).strip()

            # Raqamni ajratib olish
            number = extract_number_from_id(id_value)

            # Transport turini aniqlash
            transport_type = get_transport_type_from_id(id_value)

            # Foydalanuvchini topish
            user = None
            if number:
                user = self._find_user_by_number(number)

            # Sana
            created_at = row.get('OMBORDA', '')
            if not created_at or str(created_at).strip() in ['', 'None', 'null']:
                created_at = timezone.now()

            row['track_code'] = track_code
            row['flight_name'] = flight_name
            row['created_at'] = created_at

            # ✅ Foydalanuvchi topilsa - bog'laymiz, topilmasa - user = None qoldiramiz
            if user:
                row['user'] = user.pk
                row['status'] = 'Omborda'
                self._imported_count += 1
            else:
                # ✅ Foydalanuvchi topilmadi - user = None, status "Kutilmoqda"
                row['user'] = None  # null bo'lishi mumkin
                row['status'] = 'Kutilmoqda'
                self._pending_count += 1
                self._pending_cargos.append({
                    'track_code': track_code,
                    'id_value': id_value,
                    'number': number,
                    'transport_type': transport_type,
                })

            return True  # ✅ Har doim True qaytaramiz, hech qanday qatorni o'tkazib yubormaymiz

        except Exception as e:
            print(f"Qatorni qayta ishlashda xatolik: {e}")
            return False  # Faqat xatolik bo'lsa o'tkazib yuboramiz

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Qatorni o'tkazib yuborish kerakligini tekshirish"""
        return False  # Hech qanday qatorni o'tkazib yubormaymiz

    def get_instance(self, instance_loader, row):
        """Mavjud instanceni topish - track_code bo'yicha qidiramiz"""
        track_code = row.get('track_code')
        if track_code:
            try:
                return self._meta.model.objects.get(track_code=track_code)
            except self._meta.model.DoesNotExist:
                return None
        return None

    def before_save_instance(self, instance, row, **kwargs):
        """Instanceni saqlashdan oldin"""
        if self.request and instance.user:
            if not instance.pk:  # Yangi yuk
                instance.created_by = self.request.user
                instance.warehouse_admin = self.request.user
            instance.updated_by = self.request.user

    def after_import(self, dataset, result, **kwargs):
        """Import tugagach, natijalarni chiqarish"""
        message = f"""
        ╔══════════════════════════════════════════════════════════╗
        ║                    IMPORT NATIJALARI                      ║
        ╠══════════════════════════════════════════════════════════╣
        ║  ✅ Muvaffaqiyatli import qilingan: {self._imported_count} ta yuk
        ║  ⏳ Kutilayotgan yuklar (foydalanuvchi topilmadi): {self._pending_count} ta yuk
        ╚══════════════════════════════════════════════════════════╝
        """
        print(message)

        if self._pending_cargos:
            print("\n⚠️ Foydalanuvchisi topilmagan yuklar:")
            for cargo in self._pending_cargos[:10]:  # Faqat birinchi 10 ta
                print(
                    f"   📦 {cargo['track_code']} | ID: {cargo['id_value']} | Raqam: {cargo['number']} | Tur: {cargo.get('transport_type', '-')}")
            if len(self._pending_cargos) > 10:
                print(f"   ... va {len(self._pending_cargos) - 10} ta yuk")


# --- 2. Asosiy Admin klassi ---
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
        """Resource ga request ni uzatish"""
        kwargs = super().get_resource_kwargs(request, *args, **kwargs)
        self.resource_class.request = request
        return kwargs

    def display_user_info(self, obj):
        """Foydalanuvchi ma'lumotlarini chiroyli ko'rsatish"""
        if obj.user:
            return format_html(
                '<span style="font-weight: bold; background-color: #e8f4fd; padding: 2px 8px; border-radius: 4px;">'
                '👤 {}<br><span style="font-size: 11px; color: #666;">({})</span></span>',
                obj.user.user_id if obj.user.user_id else '-',
                obj.user.get_full_name() or obj.user.phone or '-'
            )
        else:
            return format_html(
                '<span style="color: #e74c3c; background-color: #fef5f5; padding: 2px 8px; border-radius: 4px;">'
                '⚠️ Foydalanuvchi topilmadi<br><span style="font-size: 10px;">Kutilmoqda</span></span>'
            )

    display_user_info.short_description = "Foydalanuvchi"

    def get_transport_badge(self, obj):
        """Transport turini badge ko'rinishida ko'rsatish"""
        if obj.user and obj.user.user_id:
            user_id = obj.user.user_id.upper()
            if 'UT' in user_id:
                return format_html(
                    '<span style="background-color: #3498db; color: white; padding: 3px 10px; '
                    'border-radius: 12px; font-size: 11px;">✈️ AVIA</span>'
                )
            elif 'A' in user_id:
                return format_html(
                    '<span style="background-color: #e67e22; color: white; padding: 3px 10px; '
                    'border-radius: 12px; font-size: 11px;">🚚 AVTO</span>'
                )
        return format_html(
            '<span style="background-color: #95a5a6; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px;">❓ ANIQLANMAGAN</span>'
        )

    get_transport_badge.short_description = "Transport"

    def colored_status(self, obj):
        """Statusni rangli ko'rsatish"""
        colors = {
            'Omborda': '#f39c12',
            'Yo\'lda': '#3498db',
            'Punktda': '#9b59b6',
            'Topshirildi': '#27ae60',
            'Kutilmoqda': '#e74c3c'  # Yangi status
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 20px; font-weight: bold; font-size: 11px; display: inline-block;">{}',
            colors.get(obj.status, '#95a5a6'),
            obj.status
        )

    colored_status.short_description = "Holati"

    def get_responsible_admin(self, obj):
        """Mas'ul adminni ko'rsatish"""
        admin_map = {
            'Omborda': obj.warehouse_admin,
            'Yo\'lda': obj.onway_admin,
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
        """Modelni saqlashda adminlarni avtomatik belgilash"""
        if not change and obj.user:
            obj.created_by = request.user

        if obj.user:
            if 'status' in form.changed_data or not change:
                if obj.status == 'Omborda':
                    obj.warehouse_admin = request.user
                elif obj.status == 'Yo\'lda':
                    obj.onway_admin = request.user
                elif obj.status == 'Punktda':
                    obj.arrived_admin = request.user
                elif obj.status == 'Topshirildi':
                    obj.delivered_admin = request.user
                    obj.delivered_at = timezone.now()

            obj.updated_by = request.user
        else:
            # Foydalanuvchisi yo'q yuklar uchun
            obj.status = 'Kutilmoqda'

        super().save_model(request, obj, form, change)

    def get_import_formats(self):
        from import_export.formats.base_formats import XLSX, CSV
        return [XLSX, CSV]


# --- 3. Modellarni registratsiya qilish ---
@admin.register(Cargo)
class AllCargoAdmin(BaseCargoAdmin):
    """Barcha yuklar"""

    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(WarehouseCargo)
class WarehouseCargoAdmin(BaseCargoAdmin):
    """Ombordagi yuklar"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Omborda')

    actions = ['make_onway']

    @admin.action(description="🚚 Yo'lga chiqarish")
    def make_onway(self, request, queryset):
        updated = queryset.update(
            status='Yo\'lda',
            onway_admin=request.user,
            updated_by=request.user
        )
        self.message_user(request, f"{updated} ta yuk yo'lga chiqarildi.")


@admin.register(OnWayCargo)
class OnWayCargoAdmin(BaseCargoAdmin):
    """Yo'ldagi yuklar"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Yo\'lda')

    actions = ['make_arrived']

    @admin.action(description="📍 Punktga yetkazish")
    def make_arrived(self, request, queryset):
        updated = queryset.update(
            status='Punktda',
            arrived_admin=request.user,
            updated_by=request.user
        )
        self.message_user(request, f"{updated} ta yuk punktga yetkazildi.")


@admin.register(ArrivedCargo)
class ArrivedCargoAdmin(BaseCargoAdmin):
    """Punktdagi yuklar"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Punktda')

    actions = ['make_delivered']

    @admin.action(description="✅ Topshirildi")
    def make_delivered(self, request, queryset):
        updated = queryset.update(
            status='Topshirildi',
            delivered_admin=request.user,
            delivered_at=timezone.now(),
            updated_by=request.user
        )
        self.message_user(request, f"{updated} ta yuk topshirildi deb belgilandi.")


@admin.register(DeliveredCargo)
class DeliveredCargoAdmin(BaseCargoAdmin):
    """Topshirilgan yuklar"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Topshirildi')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False