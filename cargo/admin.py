from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin

from accounts.forms import MyUserCreationForm
from .models import Cargo, WarehouseCargo, OnWayCargo, ArrivedCargo, DeliveredCargo, SupportMessage, TutorialVideo, \
    CalculationRequest
from accounts.models import User


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
        if dataset.headers:
            if '追踪代码' not in dataset.headers:
                for i in range(len(dataset)):
                    row_values = [str(x).strip() for x in dataset[i]]
                    if '追踪代码' in row_values:
                        dataset.headers = row_values
                        for _ in range(i + 1):
                            dataset.pop(0)
                        break

    def before_import_row(self, row, **kwargs):
        track = row.get('追踪代码')
        if not track:
            return None

        row['status'] = 'Omborda'


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    fk_name = 'user'
    extra = 1
    fields = ('message', 'image')
    readonly_fields = ('timestamp_ms', 'display_image')
    can_delete = False

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" style="border-radius:5px;"/>', obj.image.url)
        return "-"

    display_image.short_description = 'Rasm'

    @staticmethod
    def save_formset(request, formset):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.admin = request.user
                instance.is_from_admin = True
            instance.save()
        formset.save_m2m()


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class MyUserAdmin(BaseUserAdmin):
    inlines = [SupportMessageInline]
    list_display = ('id', 'user_id', 'phone', 'first_name', 'is_staff')
    search_fields = ('user_id', 'phone', 'first_name')
    readonly_fields = ('date_joined', 'last_login', 'user_id',)

    ordering = ('id',)

    fieldsets = (
        (None, {'fields': ('password',)}),
        ('Shaxsiy ma\'lumotlar',
         {'fields': ('first_name', 'last_name', 'phone', 'user_id', 'jshshir', 'passport_series', 'birth_date')}),
        ('Huquqlar', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('Muhim sanalar', {'fields': ('last_login', 'date_joined')}),
    )

    add_form = MyUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'user_id', 'first_name', 'last_name', 'is_staff', 'password'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs['form'] = self.add_form
        return super().get_form(request, obj, **kwargs)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, SupportMessage):
                if not instance.pk:
                    instance.admin = request.user
                    instance.is_from_admin = True
            instance.save()
        formset.save_m2m()


class BaseCargoAdmin(ImportExportModelAdmin):
    resource_class = CargoResource
    list_display = ('track_code', 'display_uts_id', 'colored_status', 'get_responsible_admin', 'created_at')
    search_fields = ('track_code', 'user__user_id', 'user__phone')
    autocomplete_fields = ['user']
    readonly_fields = (
        'created_by', 'updated_by', 'delivered_at', 'warehouse_admin', 'onway_admin', 'arrived_admin',
        'delivered_admin')
    list_per_page = 50

    def get_responsible_admin(self, obj):
        if obj.status == 'Topshirildi': return obj.delivered_admin
        if obj.status == 'Punktda': return obj.arrived_admin
        if obj.status == 'Yo\'lda': return obj.onway_admin
        return obj.warehouse_admin

    get_responsible_admin.short_description = "Mas'ul xodim"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            if obj.status == 'Omborda':
                obj.warehouse_admin = request.user
        else:
            if 'status' in form.changed_data:
                if obj.status == 'Yo\'lda': obj.onway_admin = request.user
                if obj.status == 'Punktda': obj.arrived_admin = request.user
                if obj.status == 'Topshirildi': obj.delivered_admin = request.user

        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

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
@admin.register(Cargo)
class AllCargoAdmin(BaseCargoAdmin):
    list_filter = ('status', 'created_at')


@admin.register(WarehouseCargo)
class WarehouseCargoAdmin(BaseCargoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Omborda')

    actions = ['send_to_way']

    @admin.action(description="Yo'lga chiqarish")
    def send_to_way(self, request, queryset):
        for cargo in queryset:
            cargo.status = 'Yo\'lda'
            cargo.onway_admin = request.user
            cargo.updated_by = request.user
            cargo.save()


@admin.register(OnWayCargo)
class OnWayCargoAdmin(BaseCargoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Yo\'lda')

    actions = ['mark_as_arrived']

    @admin.action(description="Punktga keldi deb belgilash")
    def mark_as_arrived(self, request, queryset):
        for cargo in queryset:
            cargo.status = 'Punktda'
            cargo.arrived_admin = request.user
            cargo.updated_by = request.user
            cargo.save()


@admin.register(ArrivedCargo)
class ArrivedCargoAdmin(BaseCargoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Punktda')

    actions = ['confirm_delivery']

    @admin.action(description="Topshirildi deb tasdiqlash")
    def confirm_delivery(self, request, queryset):
        for cargo in queryset:
            cargo.status = 'Topshirildi'
            cargo.delivered_at = timezone.now()
            cargo.delivered_admin = request.user
            cargo.updated_by = request.user
            cargo.save()


@admin.register(DeliveredCargo)
class DeliveredCargoAdmin(BaseCargoAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='Topshirildi')


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    fields = ('user', 'message', 'image')
    list_display = ('user', 'get_sender_display', 'message_preview', 'created_at')
    search_fields = ('user__user_id', 'message')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.admin = request.user
            obj.is_from_admin = True
        super().save_model(request, obj, form, change)

    def get_sender_display(self, obj):
        if obj.is_from_admin:
            return format_html('<b style="color: #d9534f;">Admin: {}</b>', obj.admin)
        return format_html('<b style="color: #5cb85c;">Client</b>')

    get_sender_display.short_description = "Kimdan"

    @staticmethod
    def message_preview(obj):
        if obj.message:
            return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
        return "🖼 Rasm"

@admin.register(TutorialVideo)
class TutorialVideoAdmin(admin.ModelAdmin):
    list_display = ('video_url', 'created_at')

@admin.register(CalculationRequest)
class CalculationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight', 'price', 'is_responded', 'created_at')
    list_editable = ('price', 'is_responded')
    readonly_fields = ('user', 'image', 'weight', 'length', 'width', 'height', 'comment', 'created_at')
