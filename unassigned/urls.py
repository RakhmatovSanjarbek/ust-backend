from django.urls import path
from . import views

urlpatterns = [
    path('', views.unassigned_cargo_list, name='unassigned_cargo_list'),
]