from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from core import settings
from django.utils import timezone


class Cargo(models.Model):
    TRANSPORT_CHOICES = [
        ('AVIA', 'AVIA'),
        ('AVTO', 'AVTO'),
    ]

    # mavjud fieldlar...
    transport_type = models.CharField(
        max_length=10,
        choices=TRANSPORT_CHOICES,
        null=True, blank=True,
        verbose_name="Transport turi"
    )

    STATUS_CHOICES = [
        ('Kutilmoqda', 'Kutilmoqda'),
        ('Omborda', 'Omborda'),
        ("Yo'lda", "Yo'lda"),
        ('Punktda', 'Punktda'),
        ('Topshirildi', 'Topshirildi'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cargos',
        verbose_name="Foydalanuvchi"
    )

    track_code = models.CharField(max_length=100, unique=True, verbose_name="Trek kod")
    flight_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Reys")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Kutilmoqda', verbose_name="Status")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="Omborga kelgan sana")
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # ✅ YANGI: Import paytida signalni o'chirish uchun flag
    # Bu maydon bazaga saqlanmaydi, faqat xotirada
    _skip_push_signal = False

    warehouse_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='wh_admin'
    )
    onway_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ow_admin'
    )
    arrived_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ar_admin'
    )
    delivered_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='dl_admin'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cargo_creator'
    )
    arrived_group = models.ForeignKey(
        'warehouse.ArrivedGroup', on_delete=models.CASCADE,
        null=True, blank=True, related_name='cargos',
        verbose_name="Kelganlar guruhi"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='updated_cargos',
        verbose_name="Mas'ul admin"
    )

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


@receiver(pre_save, sender=Cargo)
def cargo_status_pre_save(sender, instance, **kwargs):
    """Eski statusni saqlab qo'yamiz"""
    if instance.pk:
        try:
            instance._old_status = Cargo.objects.get(pk=instance.pk).status
        except Cargo.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Cargo)
def cargo_status_post_save(sender, instance, created, **kwargs):
    """
    ✅ TUZATILDI: Import paytida signal ishlamaydi (_skip_push_signal=True bo'lsa).
    Faqat admin paneldan YAKKA tartibda o'zgartirilganda ishlaydi.
    """
    # Import paytida bu flag True bo'ladi — signal o'tkazib yuboriladi
    if getattr(instance, '_skip_push_signal', False):
        return

    from utils.push_service import send_cargo_status_push

    if created:
        # Yangi yuk yaratildi (admin paneldan qo'lda qo'shilgan)
        if instance.user and instance.status != 'Kutilmoqda':
            send_cargo_status_push(instance)
    else:
        # Mavjud yuk statusi o'zgardi (yakka tartibda)
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            send_cargo_status_push(instance)