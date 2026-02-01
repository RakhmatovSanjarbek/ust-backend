from django.urls import path
from .views import my_cargos, mark_as_delivered
from . import views

urlpatterns = [
    path('my-cargos/', my_cargos),
    path('deliver/', mark_as_delivered),
    path('chat/', views.support_chat_view, name='support_chat'),
]