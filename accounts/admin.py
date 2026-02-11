from django.contrib import admin
from .models import User, OTPCode


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'phone', 'first_name', 'is_active')
    search_fields = ('user_id', 'phone', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff')
    readonly_fields = ('user_id',)


@admin.register(OTPCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
