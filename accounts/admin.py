from django.contrib import admin
from .models import User, OTPCode

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # 'is_verified'ni o'chirib turamiz
    list_display = ('user_id', 'phone', 'first_name', 'is_active')
    # Mana shu qator qidiruv uchun shart:
    search_fields = ('user_id', 'phone', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff')
    readonly_fields = ('user_id',)

@admin.register(OTPCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')