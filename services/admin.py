from django.contrib import admin
from django.urls import path
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import SupportMessage, TutorialVideo, CalculationRequest, WarehouseSettings, AppVersion
from accounts.models import User


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    change_list_template = 'admin/services/telegram_chat.html'
    list_display = ('user', 'message_preview', 'is_from_admin', 'created_at')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('api/users/', self.admin_site.admin_view(self.api_users), name='support_api_users'),
            path('api/messages/<int:user_id>/', self.admin_site.admin_view(self.api_messages), name='support_api_messages'),
            path('api/send/', self.api_send_wrapper, name='support_api_send'),
            path('api/mark-read/<int:user_id>/', self.admin_site.admin_view(self.api_mark_read), name='support_api_mark_read'),
        ]
        return custom_urls + urls

    @method_decorator(csrf_exempt, name='dispatch')
    def api_send_wrapper(self, request):
        return self.api_send(request)

    def api_users(self, request):
        users = User.objects.filter(chat_messages__isnull=False).distinct()
        data = []
        for user in users:
            last_msg = SupportMessage.objects.filter(user=user).last()
            unread_count = SupportMessage.objects.filter(user=user, is_from_admin=False, is_read=False).count()
            data.append({
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}".strip() or user.phone,
                'phone': user.phone,
                'user_id': user.user_id or "ID yo'q",
                'last_message': last_msg.message[:50] if last_msg and last_msg.message else ('📷 Rasm' if last_msg and last_msg.image else "Xabar yo'q"),
                'last_time': last_msg.created_at.strftime('%H:%M') if last_msg else '',
                'unread_count': unread_count,
                'avatar': f"https://ui-avatars.com/api/?background=3b82f6&color=fff&name={user.first_name}+{user.last_name}"
            })
        return JsonResponse(data, safe=False)

    def api_messages(self, request, user_id):
        try:
            messages = SupportMessage.objects.filter(user_id=user_id).order_by('created_at')
            data = [{
                'id': msg.id,
                'text': msg.message or '',
                'image': msg.image.url if msg.image else None,
                'is_admin': msg.is_from_admin,
                'time': msg.created_at.strftime('%H:%M'),
                'date': msg.created_at.strftime('%d.%m.%Y'),
            } for msg in messages]
            SupportMessage.objects.filter(user_id=user_id, is_from_admin=False, is_read=False).update(is_read=True)
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    @csrf_exempt
    def api_send(self, request):
        if request.method == 'POST':
            try:
                user_id = request.POST.get('user_id')
                message = request.POST.get('message')
                image = request.FILES.get('image')
                if not user_id:
                    return JsonResponse({'status': 'error', 'message': 'user_id required'}, status=400)
                user = get_object_or_404(User, id=user_id)
                SupportMessage.objects.create(user=user, message=message or '', image=image, is_from_admin=True)
                return JsonResponse({'status': 'ok'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    def api_mark_read(self, request, user_id):
        SupportMessage.objects.filter(user_id=user_id, is_from_admin=False, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})

    def message_preview(self, obj):
        return obj.message[:50] if obj.message else '📷'
    message_preview.short_description = "Xabar"


@admin.register(TutorialVideo)
class TutorialVideoAdmin(admin.ModelAdmin):
    list_display = ('video_url', 'created_at')


@admin.register(CalculationRequest)
class CalculationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight', 'price', 'is_responded', 'created_at')
    list_editable = ('price', 'is_responded')


@admin.register(WarehouseSettings)
class WarehouseSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Xitoy (AVIA)', {
            'fields': ('china_avia_price', 'china_avia_term', 'china_avia_phone', 'china_avia_address'),
        }),
        ('Xitoy (AVTO)', {
            'fields': ('china_auto_price', 'china_auto_term', 'china_auto_phone', 'china_auto_address'),
        }),
        ('Kontaktlar', {
            'fields': ('contact_telegram', 'contact_instagram', 'contact_phone'),
        }),
        ("To'lov ma'lumotlari", {
            'fields': ('dollar_rate', 'dollar_rate_updated_at', 'payment_card_number', 'payment_card_holder'),
        }),
        ('Olib ketish punkti', {
            'fields': ('pickup_name', 'pickup_lat', 'pickup_lng'),
        }),
    )

    def has_add_permission(self, request):
        return not WarehouseSettings.objects.exists()


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ('version', 'is_force_update', 'play_store_url', 'app_store_url', 'updated_at')

    def has_add_permission(self, request):
        return not AppVersion.objects.exists()