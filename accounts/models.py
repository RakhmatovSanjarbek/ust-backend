from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Telefon raqam kiritilishi shart')
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    username = None
    phone = models.CharField(max_length=15, unique=True)
    user_id = models.CharField(max_length=20, unique=True, editable=False)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    jshshir = models.CharField(max_length=14, null=True, blank=True)
    passport_series = models.CharField(max_length=9, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        if not self.user_id:
            # Eng oxirgi ID raqamini olish
            last_user = User.objects.all().order_by('id').last()
            next_id = 1 if not last_user else last_user.id + 1
            self.user_id = f"UTS-{str(next_id).zfill(6)}"
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_id} | {self.phone}"


class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone} uchun kod: {self.code}"