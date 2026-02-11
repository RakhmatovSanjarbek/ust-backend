from django.urls import path
from .views import (
    signin_request,
    signup,
    verify_otp,
    get_user_data,
    update_user_profile
)

urlpatterns = [
    path('signin/', signin_request),
    path('signup/', signup),
    path('verify/', verify_otp),
    path('me/', get_user_data),
    path('update/', update_user_profile),
]
