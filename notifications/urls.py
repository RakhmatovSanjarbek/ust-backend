from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_notifications, name='notifications'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('read-all/', views.mark_all_as_read, name='mark_all_read'),
    path('<int:notification_id>/read/', views.mark_as_read, name='mark_read'),
]