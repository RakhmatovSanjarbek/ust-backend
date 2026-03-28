from django.urls import path
from .views import my_cargos, mark_as_delivered
from django.urls import path, include

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('my-cargos/', my_cargos),
    path('deliver/', mark_as_delivered),
]