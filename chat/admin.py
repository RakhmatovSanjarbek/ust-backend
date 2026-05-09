from django.contrib import admin
from django.urls import path
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import ChatMessage
from accounts.models import User


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    change_list_template = 'admin/chat/telegram_chat.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('telegram-chat/', self.admin_site.admin_view(self.telegram_chat), name='telegram_chat'),
            path('api/users/', self.admin_site.admin_view(self.api_users), name='chat_api_users'),
            path('api/messages/<int:user_id>/', self.admin_site.admin_view(self.api_messages),
                 name='chat_api_messages'),
            path('api/send/', self.admin_site.admin_view(self.api_send), name='chat_api_send'),
            path('api/mark-read/<int:user_id>/', self.admin_site.admin_view(self.api_mark_read),
                 name='chat_api_mark_read'),
        ]
        return custom_urls + urls

    def telegram_chat(self, request):
        context = {
            'title': 'Telegram-stil Chat',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/chat/telegram_chat.html', context)

    def api_users(self, request):
        """Foydalanuvchilar ro'yxati"""
        users = User.objects.filter(is_staff=False).order_by('-date_joined')
        data = []

        for user in users:
            last_msg = ChatMessage.objects.filter(user=user).last()
            unread_count = ChatMessage.objects.filter(user=user, is_from_admin=False, is_read=False).count()

            data.append({
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}".strip() or user.phone,
                'phone': user.phone,
                'user_id': user.user_id or 'ID yo\'q',
                'last_message': last_msg.message[
                    :50] if last_msg and last_msg.message else '📷 Rasm' if last_msg and last_msg.image else 'Xabar yo\'q',
                'last_time': last_msg.created_at.strftime('%H:%M') if last_msg else '',
                'unread_count': unread_count,
                'avatar': f"https://ui-avatars.com/api/?background=3b82f6&color=fff&name={user.first_name}+{user.last_name}"
            })

        return JsonResponse(data, safe=False)

    def api_messages(self, request, user_id):
        """Foydalanuvchi bilan chat tarixi"""
        messages = ChatMessage.objects.filter(user_id=user_id).order_by('created_at')
        data = []

        for msg in messages:
            data.append({
                'id': msg.id,
                'text': msg.message or '',
                'image': msg.image.url if msg.image else None,
                'is_admin': msg.is_from_admin,
                'time': msg.created_at.strftime('%H:%M'),
                'date': msg.created_at.strftime('%d.%m.%Y'),
            })

        # Admin ko'rgan xabarlarni o'qilgan deb belgilash
        ChatMessage.objects.filter(user_id=user_id, is_from_admin=False, is_read=False).update(is_read=True)

        return JsonResponse(data, safe=False)

    @method_decorator(csrf_exempt)
    def api_send(self, request):
        """Xabar yuborish"""
        if request.method == 'POST':
            user_id = request.POST.get('user_id')
            message = request.POST.get('message', '')
            image = request.FILES.get('image')

            user = get_object_or_404(User, id=user_id)

            ChatMessage.objects.create(
                user=user,
                admin=request.user,
                message=message,
                image=image,
                is_from_admin=True
            )

            return JsonResponse({'status': 'ok'})

        return JsonResponse({'status': 'error'}, status=400)

    def api_mark_read(self, request, user_id):
        """Xabarlarni o'qilgan deb belgilash"""
        ChatMessage.objects.filter(user_id=user_id, is_from_admin=False, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})