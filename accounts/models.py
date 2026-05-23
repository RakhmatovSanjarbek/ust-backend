from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Telefon raqam kiritilishi shart")

        user = self.model(phone=phone, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", "approved")

        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlangan'),
        ('rejected', 'Rad etilgan'),
    )
    REJECTION_REASONS = (
        ('passport_blur', 'Pasport rasmi xira'),
        ('invalid_data', 'Ma’lumotlar xato'),
        ('fake_document', 'Hujjat haqiqiy emas'),
        ('other', 'Boshqa sabab'),
    )

    username = None

    phone = models.CharField(max_length=15, unique=True)
    user_id = models.CharField(max_length=20, unique=True, null=True, blank=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    jshshir = models.CharField(max_length=14, null=True, blank=True)
    passport_series = models.CharField(max_length=9, null=True, blank=True)
    passport_front = models.ImageField(upload_to='passports/', null=True, blank=True)
    passport_back = models.ImageField(upload_to='passports/', null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.CharField(max_length=50, choices=REJECTION_REASONS, null=True, blank=True)
    rejection_note = models.TextField(null=True, blank=True, help_text="Qo'shimcha izoh")
    last_active = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    fcm_token = models.CharField(max_length=255, null=True, blank=True, help_text="Firebase Cloud Messaging Token")

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.user_id or 'ID yoq'} | {self.phone}"


class UserRelative(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="relatives")
    full_name = models.CharField(max_length=255)
    jshshir = models.CharField(max_length=14)
    passport_series = models.CharField(max_length=9)
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.user_id} uchun)"


class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone} uchun kod: {self.code}"
