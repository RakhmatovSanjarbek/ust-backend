from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from .models import Cargo, WarehouseCargo, OnWayCargo, ArrivedCargo, DeliveredCargo, SupportMessage
from accounts.models import User


# ==========================================
# 1. IMPORT/EXPORT RESURSI (ALGORITM SAQLANDI)
# ==========================================

class CargoResource(resources.ModelResource):
    track_code = fields.Field(
        attribute='track_code',
        column_name='追踪代码'
    )
    user = fields.Field(
        attribute='user',
        column_name='客户代码',
        widget=ForeignKeyWidget(User, 'user_id')
    )

    class Meta:
        model = Cargo
        import_id_fields = ('track_code',)
        fields = ('track_code', 'user', 'status')
        skip_unchanged = True
        report_skipped = True

    def before_import(self, dataset, **kwargs):
        """
        Eski algoritmingiz: Excel ichidan sarlavhani qidirib topish va
        undan yuqoridagi bo'sh qatorlarni tozalash mantig'i saqlandi.
        """
        if dataset.headers:
            if '追踪代码' not in dataset.headers:
                # Sarlavha qatorini qidirish
                for i in range(len(dataset)):
                    row_values = [str(x).strip() for x in dataset[i]]
                    if '追踪代码' in row_values:
                        dataset.headers = row_values
                        # Sarlavhagacha bo'lgan barcha qatorlarni o'chirish
                        for _ in range(i + 1):
                            dataset.pop(0)
                        break

    def before_import_row(self, row, **kwargs):
        """
        Eski algoritmingiz: Track code bo'lmasa tashlab ketish va
        statusni 'Omborda' deb belgilash mantig'i saqlandi.
        """
        track = row.get('追踪代码')
        if not track:
            return None  # Bo'sh qatorlarni yuklamaydi

        row['status'] = 'Omborda'


# ==========================================
# 2. USER VA SUPPORT CHAT
# ==========================================

class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    fk_name = 'user'
    extra = 1
    fields = ('is_from_admin', 'message', 'display_image', 'timestamp_ms')
    readonly_fields = ('timestamp_ms', 'display_image')
    can_delete = False

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" style="border-radius:5px;"/>', obj.image.url)
        return "-"

    display_image.short_description = 'Rasm'


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class MyUserAdmin(BaseUserAdmin):
    inlines = [SupportMessageInline]
    list_display = ('id', 'user_id', 'phone', 'first_name', 'is_staff')
    search_fields = ('user_id', 'phone', 'first_name')
    readonly_fields = ('date_joined', 'last_login')

    # admin.E033 xatoligini tuzatish: 'username' o'rniga 'user_id' yoki 'id' ishlatiladi
    ordering = ('id',)

    fieldsets = (
        (None, {'fields': ('password',)}),
        ('Shaxsiy ma\'lumotlar', {'fields': ('first_name', 'last_name', 'phone', 'user_id', 'jshshir')}),
        ('Huquqlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('Muhim sanalar', {'fields': ('last_login', 'date_joined')}),
    )


# ==========================================
# 3. ASOSIY KARGO ADMIN (SKANER VA STATUSLAR)
# ==========================================

class BaseCargoAdmin(ImportExportModelAdmin):
    resource_class = CargoResource
    list_display = ('track_code', 'display_uts_id', 'colored_status', 'created_at')
    search_fields = ('track_code', 'user__user_id', 'user__phone')
    autocomplete_fields = ['user']
    readonly_fields = ('created_by', 'updated_by', 'delivered_at')
    list_per_page = 50

    def colored_status(self, obj):
        colors = {
            'Omborda': '#f39c12',
            'Yo\'lda': '#3498db',
            'Punktda': '#9b59b6',
            'Topshirildi': '#2ecc71'
        }
        status_text = obj.status if obj.status else "Noma'lum"
        return format_html(
            '<span style="color: white; background-color: {}; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#7f8c8d'), status_text
        )

    colored_status.short_description = 'Holati'

    def display_uts_id(self, obj):
        return obj.user.user_id if obj.user else "-"

    display_uts_id.short_description = 'UTS ID'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'track_code' in form.base_fields:
            form.base_fields['track_code'].help_text = format_html(
                '<div style="margin-top: 10px;">'
                '<button type="button" id="start-scanner" style="background-color: #f39c12; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold;">'
                '📷 QR/SHTRIX-KODNI SKANERLASH</button>'
                '<div id="reader" style="width: 100%; max-width: 400px; display: none; margin-top: 10px; border: 2px solid #f39c12; border-radius: 10px; overflow: hidden;"></div>'
                '</div>'
            )
        return form

    class Media:
        js = (
            'https://unpkg.com/html5-qrcode',
            'admin/js/cargo_scanner.js',
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Registratsiyalar
@admin.register(Cargo)
class AllCargoAdmin(BaseCargoAdmin):
    list_filter = ('status', 'created_at')


@admin.register(WarehouseCargo)
class WarehouseCargoAdmin(BaseCargoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Omborda')

    actions = ['send_to_way']

    @admin.action(description="Tanlanganlarni 'Yo'lga' chiqarish")
    def send_to_way(self, request, queryset):
        queryset.update(status='Yo\'lda', updated_by=request.user)


@admin.register(OnWayCargo)
class OnWayCargoAdmin(BaseCargoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Yo\'lda')

    actions = ['mark_as_arrived']

    @admin.action(description="Tanlanganlarni 'Punktga keldi' deb belgilash")
    def mark_as_arrived(self, request, queryset):
        queryset.update(status='Punktda', updated_by=request.user)


@admin.register(ArrivedCargo)
class ArrivedCargoAdmin(BaseCargoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Punktda')

    actions = ['confirm_delivery']

    @admin.action(description="✅ TOPSHIRISHNI TASDIQLASH")
    def confirm_delivery(self, request, queryset):
        queryset.update(status='Topshirildi', delivered_at=timezone.now(), updated_by=request.user)


@admin.register(DeliveredCargo)
class DeliveredCargoAdmin(BaseCargoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Topshirildi')


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_preview', 'created_at')
    search_fields = ('user__user_id', 'message')

    def message_preview(self, obj):
        if obj.message:
            return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
        return "🖼 Rasm yuborilgan"