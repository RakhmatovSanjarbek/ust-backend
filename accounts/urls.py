from django.urls import path
from django.urls import path, include
from .views import (
    signin_request,
    signup,
    verify_otp,
    get_user_data,
    update_user_profile,
    delete_account,
    manage_relatives,
    delete_relative
)

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('signin/', signin_request),
    path('signup/', signup),
    path('verify/', verify_otp),
    path('me/', get_user_data),
    path('update/', update_user_profile),
    path('delete-account/', delete_account),
    path('relatives/', manage_relatives),
    path('relatives/<int:pk>/', delete_relative),
]
