from django.urls import path
from . import views

urlpatterns = [
    path('', views.flight_list, name='flight_list'),
]
