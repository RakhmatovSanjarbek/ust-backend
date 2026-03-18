from django.db import models
import time
from accounts.models import User


class SupportMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_responses')
    message = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    is_from_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    timestamp_ms = models.BigIntegerField(editable=False)

    def save(self, *args, **kwargs):
        if self.admin:
            self.is_from_admin = True
        if not self.timestamp_ms:
            self.timestamp_ms = int(time.time() * 1000)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat xabari"
        verbose_name_plural = "Chat xabarlari"

class TutorialVideo(models.Model):
    video_url = models.URLField(verbose_name="YouTube video havolasi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.video_url

    class Meta:
        verbose_name = "Video darslik"
        verbose_name_plural = "Video darslik"

class CalculationRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='cargo_calc/')
    weight = models.FloatField()
    length = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    comment = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admin_note = models.TextField(blank=True, null=True)
    is_responded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.weight}kg"

    class Meta:
        verbose_name = "Kalkulator (Yuk)"
        verbose_name_plural = "Kalkulator (Yuk)"

class WarehouseSettings(models.Model):
    # Xitoy (AVIA)
    china_avia_phone = models.CharField(max_length=255, verbose_name="Xitoy (AVIA) telefon")
    china_avia_address = models.TextField(verbose_name="Xitoy (AVIA) manzili")
    china_avia_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Xitoy (AVIA) narxi ($)")
    china_avia_term = models.CharField(max_length=100, verbose_name="Xitoy (AVIA) muddati (kun)")

    # Xitoy (AVTO)
    china_auto_phone = models.CharField(max_length=255, verbose_name="Xitoy (AVTO) telefon")
    china_auto_address = models.TextField(verbose_name="Xitoy (AVTO) manzili")
    china_auto_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Xitoy (AVTO) narxi ($)")
    china_auto_term = models.CharField(max_length=100, verbose_name="Xitoy (AVTO) muddati (kun)")

    # Kontaktlar
    contact_telegram = models.CharField(max_length=255, verbose_name="Telegram link")
    contact_instagram = models.CharField(max_length=255, verbose_name="Instagram link")
    contact_phone = models.CharField(max_length=255, verbose_name="Asosiy telefon")

    class Meta:
        verbose_name = "Ombor va Kontakt"
        verbose_name_plural = "Ombor va Kontak"