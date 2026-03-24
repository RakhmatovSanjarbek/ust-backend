import re
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field

from accounts.models import User
from .models import Cargo, WarehouseCargo, OnWayCargo, ArrivedCargo, DeliveredCargo


# --- 1. Optimallashtirilgan Resource ---
class CargoResource(resources.ModelResource):
    # Import qilishda ishlatiladigan maydonlar
    track_code = Field(attribute='track_code', column_name='TREK RAQAM')
    flight_name = Field(attribute='flight_name', column_name='REYS')
    id_field = Field(attribute='user', column_name='ID')
    created_at = Field(attribute='created_at', column_name='OMBORDA')

    class Meta:
        model = Cargo
        # import_id_fields ni bo'sh qilib qo'yamiz, chunki trek code orqali tekshirishni o'zimiz qilamiz
        import_id_fields = ()
        fields = ('track_code', 'flight_name', 'created_at', 'status', 'user')
        skip_unchanged = True
        report_skipped = True
        export_order = ('track_code', 'flight_name', 'created_at', 'status', 'user')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_cache = {}  # Foydalanuvchi cache'i
        self._skipped_rows = []  # O'tkazib yuborilgan qatorlar
        self._imported_count = 0
        self._skipped_count = 0
        self.request = None  # Request ni saqlash uchun

    def get_import_id_fields(self):
        """Import ID fieldlarini qaytarish - bo'sh list qaytaramiz"""
        return []

    def _extract_uts_number(self, id_value):
        """
        ID dan faqat raqamli qismni ajratib oladi
        UT-002 -> 002
        A-002 -> 002
        UTS-002 -> 002
        """
        if not id_value:
            return None

        id_str = str(id_value).strip()
        # Faqat raqamlarni topish (oxirgi 3-4 raqam)
        match = re.search(r'(\d{3,4})$', id_str)
        if match:
            return match.group(1)
        return None

    def _get_user_by_uts(self, uts_number):
        """
        UTS raqami bo'yicha foydalanuvchini topadi
        """
        if not uts_number:
            return None

        # Cache'dan tekshirish
        if uts_number in self._user_cache:
            return self._user_cache[uts_number]

        # UTS-### formatida qidirish
        user = None

        # Bir nechta formatlarda qidirish
        patterns = [
            f"UTS-{uts_number}",
            f"UTS{uts_number}",
            f"UTS {uts_number}",
        ]

        # Agar 3 xonali bo'lsa, 4 xonali formatda ham qidirish
        if len(uts_number) == 3:
            patterns.extend([
                f"UTS-0{uts_number}",
                f"UTS0{uts_number}",
            ])

        for pattern in patterns:
            user = User.objects.filter(user_id__iexact=pattern).first()
            if user:
                break

        # Agar topilmasa, raqamni o'z ichiga olganlarni qidirish
        if not user:
            user = User.objects.filter(user_id__icontains=uts_number).first()

        # Cache'ga saqlash
        self._user_cache[uts_number] = user
        return user

    def before_import(self, dataset, **kwargs):
        """Import boshlanishida statistikani tozalash"""
        self._user_cache = {}
        self._skipped_rows = []
        self._imported_count = 0
        self._skipped_count = 0

        # Datasetni tozalash - bo'sh qatorlarni olib tashlash
        rows_to_remove = []
        for i, row in enumerate(dataset.dict):
            # Agar barcha ustunlar bo'sh bo'lsa, qatorni olib tashlash
            if all(not str(v).strip() or str(v).strip().lower() in ['none', 'null', ''] for v in row.values()):
                rows_to_remove.append(i)

        # Bo'sh qatorlarni orqadan olib tashlash
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
                self._skipped_count += 1
                self._skipped_rows.append({
                    'track_code': track_code,
                    'reason': 'Trek kodi bo\'sh'
                })
                return False

            # Reys nomi
            flight_name = row.get('REYS', 'R-125')
            if flight_name:
                flight_name = str(flight_name).strip()
            else:
                flight_name = 'R-125'

            # ID (UT-002 yoki A-002)
            id_value = row.get('ID', '')
            if id_value:
                id_value = str(id_value).strip()

            uts_number = self._extract_uts_number(id_value)

            # Foydalanuvchini topish
            user = None
            if uts_number:
                user = self._get_user_by_uts(uts_number)

            # Agar foydalanuvchi topilmasa, bu qatorni o'tkazib yuborish
            if not user:
                self._skipped_count += 1
                self._skipped_rows.append({
                    'track_code': track_code,
                    'id_value': id_value,
                    'uts_number': uts_number,
                    'reason': f'Foydalanuvchi topilmadi (ID: {id_value})'
                })
                return False

            # Sana
            created_at = row.get('OMBORDA', '')
            if created_at:
                created_at = str(created_at).strip()
            else:
                created_at = str(timezone.now())

            # Row ma'lumotlarini to'ldirish
            row['track_code'] = track_code
            row['flight_name'] = flight_name
            row['user'] = user.pk
            row['created_at'] = created_at
            row['status'] = 'Omborda'

            self._imported_count += 1
            return True

        except Exception as e:
            self._skipped_count += 1
            self._skipped_rows.append({
                'row': row,
                'error': str(e),
                'reason': f'Xatolik: {str(e)}'
            })
            return False

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Qatorni o'tkazib yuborish kerakligini tekshirish"""
        # Agar user mavjud bo'lmasa, o'tkazib yuborish
        if row.get('user') is None:
            return True
        return False

    def get_instance(self, instance_loader, row):
        """
        Mavjud instanceni topish - track_code bo'yicha qidiramiz
        """
        track_code = row.get('track_code')
        if track_code:
            try:
                return self._meta.model.objects.get(track_code=track_code)
            except self._meta.model.DoesNotExist:
                return None
        return None

    def before_save_instance(self, instance, row, **kwargs):
        """Instanceni saqlashdan oldin admin ma'lumotlarini biriktirish"""
        if self.request:
            if not instance.pk:  # Yangi yuk
                instance.created_by = self.request.user
                instance.warehouse_admin = self.request.user
            instance.updated_by = self.request.user

    def after_import(self, dataset, result, **kwargs):
        """Import tugagach, natijalarni chiqarish"""
        # Hech qanday o'zgartirish qilmaymiz, faqat xabarni chiqaramiz
        if self._skipped_rows:
            print(f"\n{'=' * 50}")
            print(f"IMPORT NATIJALARI:")
            print(f"  Muvaffaqiyatli import: {self._imported_count} ta")
            print(f"  O'tkazib yuborilgan: {self._skipped_count} ta")
            print(f"{'=' * 50}")

            if self._skipped_rows:
                print("\nO'tkazib yuborilgan qatorlar sabablari:")
                reasons = {}
                for skipped in self._skipped_rows:
                    reason = skipped.get('reason', 'Noma\'lum sabab')
                    reasons[reason] = reasons.get(reason, 0) + 1

                for reason, count in reasons.items():
                    print(f"  - {reason}: {count} ta")


# --- 2. Asosiy Admin klassi ---
class BaseCargoAdmin(ImportExportModelAdmin):
    resource_class = CargoResource

    list_display = (
        'track_code', 'display_uts_id', 'flight_name',
        'colored_status', 'created_at', 'get_responsible_admin'
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
        # Resource klassiga request ni biriktirish
        self.resource_class.request = request
        return kwargs

    def display_uts_id(self, obj):
        """UTS ID ni chiroyli ko'rsatish"""
        if obj.user and obj.user.user_id:
            return format_html(
                '<span style="font-weight: bold; background-color: #f0f0f0; '
                'padding: 2px 8px; border-radius: 4px;">{}</span>',
                obj.user.user_id
            )
        return format_html('<span style="color: #e74c3c;">-</span>')

    display_uts_id.short_description = "UTS ID"

    def colored_status(self, obj):
        """Statusni rangli ko'rsatish"""
        colors = {
            'Omborda': '#f39c12',  # To'q sariq
            'Yo\'lda': '#3498db',  # Moviy
            'Punktda': '#9b59b6',  # Siyohrang
            'Topshirildi': '#27ae60'  # Yashil
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 20px; font-weight: bold; font-size: 11px; display: inline-block;">{}</span>',
            colors.get(obj.status, '#95a5a6'), obj.status
        )

    colored_status.short_description = "Holati"

    def get_responsible_admin(self, obj):
        """Mas'ul adminni ko'rsatish"""
        admin_map = {
            'Omborda': obj.warehouse_admin,
            'Yo\'lda': obj.onway_admin,
            'Punktda': obj.arrived_admin,
            'Topshirildi': obj.delivered_admin
        }

        admin = admin_map.get(obj.status)
        if admin:
            name = admin.get_full_name() or admin.first_name or str(admin.phone) or admin.username
            return format_html(
                '<span style="color: #2c3e50;">👤 {}</span>',
                name[:30]  # Uzun nomlarni kesish
            )
        return format_html('<span style="color: #bdc3c7;">⚪ Belgilanmagan</span>')

    get_responsible_admin.short_description = "Mas'ul Admin"

    def save_model(self, request, obj, form, change):
        """Modelni saqlashda adminlarni avtomatik belgilash"""
        if not change:
            obj.created_by = request.user

        # Status o'zgargan bo'lsa, tegishli adminni yozish
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
        super().save_model(request, obj, form, change)

    def get_import_formats(self):
        """Import formatlarini belgilash"""
        from import_export.formats.base_formats import XLSX, CSV
        return [XLSX, CSV]


# --- 3. Modellarni registratsiya qilish ---
@admin.register(Cargo)
class AllCargoAdmin(BaseCargoAdmin):
    """Barcha yuklar"""
    list_display = BaseCargoAdmin.list_display + ('get_transport_type',)

    def get_transport_type(self, obj):
        """Transport turini aniqlash"""
        if obj.user and obj.user.user_id:
            if 'UT' in obj.user.user_id.upper():
                return '✈️ Avia'
            if 'A' in obj.user.user_id.upper():
                return '🚚 Avto'
        return '-'

    get_transport_type.short_description = 'Transport turi'


@admin.register(WarehouseCargo)
class WarehouseCargoAdmin(BaseCargoAdmin):
    """Ombordagi yuklar"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Omborda')

    actions = ['make_onway']

    @admin.action(description="🚚 Yo'lga chiqarish")
    def make_onway(self, request, queryset):
        """Yuklarni yo'lga chiqarish"""
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
        """Yuklarni punktga yetkazish"""
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
        """Yuklarni topshirilgan deb belgilash"""
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