from django.db import models
from django.utils import timezone
from core import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('Omborda', '📦 Omborda'),
        ("Yo'lda", '🚚 Yo\'lda'),
        ('Punktda', '📍 Punktda'),
        ('Topshirildi', '✅ Topshirildi'),
        ('Kutilmoqda', '⏳ Kutilmoqda'),
        ('Umumiy', '📢 Umumiy'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Foydalanuvchi"
    )
    title = models.CharField(max_length=255, verbose_name="Sarlavha")
    body = models.TextField(verbose_name="Matn")
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='Umumiy',
        verbose_name="Turi"
    )
    # Qaysi yukka tegishli (ixtiyoriy)
    cargo_id = models.IntegerField(null=True, blank=True, verbose_name="Yuk ID")
    track_code = models.CharField(max_length=100, null=True, blank=True, verbose_name="Trek kodi")

    is_read = models.BooleanField(default=False, verbose_name="O'qilganmi")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Yuborilgan vaqt")

    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} | {self.title} | {'✅' if self.is_read else '🔵'}"