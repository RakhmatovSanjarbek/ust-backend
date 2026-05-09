from django.urls import path
from . import admin as chat_admin
from . import views

urlpatterns = [
    # Admin uchun (Django admin interfeysi)
    path('telegram-chat/', chat_admin.ChatMessageAdmin.telegram_chat, name='telegram_chat'),
    path('api/users/', chat_admin.ChatMessageAdmin.api_users, name='chat_api_users'),
    path('api/messages/<int:user_id>/', chat_admin.ChatMessageAdmin.api_messages, name='chat_api_messages'),
    path('api/send/', chat_admin.ChatMessageAdmin.api_send, name='chat_api_send'),
    path('api/mark-read/<int:user_id>/', chat_admin.ChatMessageAdmin.api_mark_read, name='chat_api_mark_read'),

    # ========== MOBILE (FLUTTER) UCHUN ==========
    path('api/my-messages/', views.get_my_messages, name='my_messages'),
    path('api/send-message/', views.send_user_message, name='send_user_message'),
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
    path('api/mark-read/', views.mark_messages_read, name='mark_read'),
]