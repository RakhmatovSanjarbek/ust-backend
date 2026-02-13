from django.urls import path
from .views import my_cargos, mark_as_delivered, VideoListView, CalculationCreateListView
from . import views

urlpatterns = [
    path('my-cargos/', my_cargos),
    path('deliver/', mark_as_delivered),
    path('chat/', views.support_chat_view, name='support_chat'),
    path('videos/', VideoListView.as_view()),
    path('calculator/', CalculationCreateListView.as_view()),
]