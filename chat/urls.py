from django.urls import path
from . import views

urlpatterns = [
    path('api/my-messages/', views.get_my_messages, name='my_messages'),
    path('api/send-message/', views.send_user_message, name='send_user_message'),
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
    path('api/mark-read/', views.mark_messages_read, name='mark_read'),
]