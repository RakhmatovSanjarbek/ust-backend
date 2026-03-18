from django.urls import path
from . import views
from .views import get_warehouse_info

urlpatterns = [
    path('chat/', views.support_chat_view, name='support_chat'),
    path('videos/', views.VideoListView.as_view(), name='video_list'),
    path('calculator/', views.CalculationCreateListView.as_view(), name='calculator'),
    path('services-info/', get_warehouse_info, name='services-info'),
]