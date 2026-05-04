from django.contrib import admin
from django.utils.html import format_html
from .models import User, OTPCode, UserRelative


# --- PROXY MODEL ---
class UserApplication(User):
    class Meta:
        proxy = True
        verbose_name = "Ro'yxatdan o'tish so'rovi"
        verbose_name_plural = "Ro'yxatdan o'tish so'rovlari"


# --- INLINES ---
class UserRelativeInline(admin.TabularInline):
    model = UserRelative
    extra = 1


# --- MIXIN (Rasmlarni ko'rsatish uchun yordamchi) ---
class UserAdminMixin:
    def passport_front_preview(self, obj):
        if obj.passport_front:
            return format_html(
                '<img src="{}" style="max-height: 200px; border-radius: 10px; border: 1px solid #ccc;"/>',
                obj.passport_front.url)
        return "Rasm yuklanmagan"

    def passport_back_preview(self, obj):
        if obj.passport_back:
            return format_html(
                '<img src="{}" style="max-height: 200px; border-radius: 10px; border: 1px solid #ccc;"/>',
                obj.passport_back.url)
        return "Rasm yuklanmagan"

    passport_front_preview.short_description = "Pasport (Oldi)"
    passport_back_preview.short_description = "Pasport (Orqa)"


# --- 1. ARIZALAR ADMINI ---
@admin.register(UserApplication)
class UserApplicationAdmin(admin.ModelAdmin, UserAdminMixin):
    def get_queryset(self, request):
        return super().get_queryset(request).exclude(status='approved')

    list_display = ('phone', 'first_name', 'last_name', 'status', 'date_joined')
    list_filter = ('status', 'rejection_reason')
    search_fields = ('phone', 'first_name', 'last_name', 'jshshir')

    # Arizani ko'rib chiqishda hamma ma'lumotlar ko'rinishi uchun
    fields = (
        'phone', 'first_name', 'last_name', 'jshshir',
        'passport_series', 'birth_date', 'address',
        'passport_front_preview', 'passport_front',
        'passport_back_preview', 'passport_back',
        'status', 'rejection_reason', 'rejection_note', 'user_id'
    )
    readonly_fields = ('passport_front_preview', 'passport_back_preview')

    def save_model(self, request, obj, form, change):
        if obj.status == 'approved':
            # 1. Agar ID qo'lda yozilmagan bo'lsa, avtomatik generatsiya qilamiz
            if not obj.user_id:
                # UTS- bilan boshlanadigan barcha foydalanuvchilarni olamiz
                all_users = User.objects.filter(user_id__startswith="UTS-")

                max_num = 100  # Agar baza bo'sh bo'lsa, keyingisi 0101 bo'lishi uchun

                for user in all_users:
                    try:
                        # 'UTS-0101' -> split('-') -> ['UTS', '0101'] -> int('0101') -> 101
                        num_part = int(user.user_id.split("-")[1])
                        if num_part > max_num:
                            max_num = num_part
                    except (IndexError, ValueError):
                        # Agar ID formati noto'g'ri bo'lsa, tashlab o'tamiz
                        continue

                next_num = max_num + 1
                # :04d formati raqamni 4 ta xonali qilib to'ldiradi (masalan: 0101, 0102)
                obj.user_id = f"UTS-{next_num:04d}"

            # 2. Foydalanuvchini faollashtirish
            obj.is_active = True
            # Tasdiqlanganda rad etish sabablarini tozalaymiz
            obj.rejection_reason = None
            obj.rejection_note = None

        elif obj.status == 'rejected':
            # Rad etilganda foydalanuvchi tizimga kira olmasligi uchun (ixtiyoriy)
            # obj.is_active = False
            pass

        super().save_model(request, obj, form, change)


# --- 2. ASOSIY FOYDALANUVCHILAR ADMINI ---
@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin, UserAdminMixin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='approved')

    list_display = ('user_id', 'phone', 'first_name', 'last_name', 'is_active')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('user_id', 'phone', 'first_name', 'last_name', 'jshshir')
    inlines = [UserRelativeInline]

    readonly_fields = ('last_active', 'passport_front_preview', 'passport_back_preview')

    fieldsets = (
        ("Shaxsiy ma'lumotlar", {
            'fields': ('user_id', 'phone', 'first_name', 'last_name', 'birth_date', 'address')
        }),
        ("Hujjatlar", {
            'fields': (
                'jshshir',
                'passport_series',
                'passport_front_preview', 'passport_front',
                'passport_back_preview', 'passport_back'
            )
        }),
        ("Holat va Huquqlar", {
            'fields': ('status', 'is_active', 'is_staff', 'is_superuser')
        }),
        ("Vaqtlar", {
            'fields': ('last_active', 'date_joined')
        }),
    )


# --- 3. OTP KODLAR ADMINI ---
@admin.register(OTPCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at')
    search_fields = ('user__phone', 'code')