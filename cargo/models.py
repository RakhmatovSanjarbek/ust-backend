from django.db import models

from core import settings
from django.utils import timezone


class Cargo(models.Model):
    STATUS_CHOICES = [
        ('Omborda', 'Omborda'),
        ('Yo\'lda', 'Yo\'lda'),
        ('Punktda', 'Punktda'),
        ('Topshirildi', 'Topshirildi'),
    ]
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='cargos',
                             verbose_name="Foydalanuvchi")
    track_code = models.CharField(max_length=100, unique=True, verbose_name="Trek kod")
    flight_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Reys")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Omborda', verbose_name="Status")

    # Omborga kelgan sana (Exceldan keladi yoki hozirgi vaqt)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Omborga kelgan sana")
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    warehouse_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='wh_admin')
    onway_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='ow_admin')
    arrived_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='ar_admin')
    delivered_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='dl_admin')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='cargo_creator')
    arrived_group = models.ForeignKey(
        'warehouse.ArrivedGroup',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cargos',
        verbose_name="Kelganlar guruhi"
    )
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='updated_cargos', verbose_name="Mas'ul admin")

    def __str__(self):
        return f"{self.track_code} - {self.status}"

    class Meta:
        verbose_name = "Yuk"
        verbose_name_plural = "Yuklar"


class WarehouseCargo(Cargo):
    class Meta:
        proxy = True
        verbose_name = "Ombordagi yuk"
        verbose_name_plural = "Ombordagi yuklar"


class OnWayCargo(Cargo):
    class Meta:
        proxy = True
        verbose_name = "Yo'ldagi yuk"
        verbose_name_plural = "Yo'ldagi yuklar"


class ArrivedCargo(Cargo):
    class Meta:
        proxy = True
        verbose_name = "Punkda (Topshirish)"
        verbose_name_plural = "Punktda (Topshirish)"


class DeliveredCargo(Cargo):
    class Meta:
        proxy = True
        verbose_name = "Topshirilgan yuk"
        verbose_name_plural = "Topshirilgan yuklar"
