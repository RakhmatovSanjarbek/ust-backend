from django.contrib import admin
from django.utils.html import format_html

from services.models import SupportMessage, TutorialVideo, CalculationRequest, WarehouseSettings


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

@admin.register(WarehouseSettings)
class WarehouseSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Xitoy (AVIA)', {
            'fields': ('china_avia_price', 'china_avia_term', 'china_avia_phone', 'china_avia_address')
        }),
        ('Xitoy (AVTO)', {
            'fields': ('china_auto_price', 'china_auto_term', 'china_auto_phone', 'china_auto_address')
        }),
        ('Kontaktlar', {
            'fields': ('contact_telegram', 'contact_instagram', 'contact_phone')
        }),
    )

    def has_add_permission(self, request):
        # Faqat 1 ta yozuv bo'lishini ta'minlaydi
        return not WarehouseSettings.objects.exists()