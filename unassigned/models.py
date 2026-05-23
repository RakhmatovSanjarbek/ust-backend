from django.db import models
from django.utils import timezone


class UnassignedCargo(models.Model):
    """Kodsiz tovarlar — foydalanuvchiga biriktirilmagan yuklar"""
    track_code = models.CharField(max_length=100, unique=True, verbose_name="Trek kodi")
    flight_name = models.CharField(max_length=100, verbose_name="Reys raqami")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Kelgan sana")
    note = models.TextField(null=True, blank=True, verbose_name="Izoh")

    class Meta:
        verbose_name = "Kodsiz tovar"
        verbose_name_plural = "Kodsiz tovarlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.track_code} | {self.flight_name}"