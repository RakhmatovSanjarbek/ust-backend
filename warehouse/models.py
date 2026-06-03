# warehouse/models.py
# Mavjud models.py ga quyidagi fieldlarni qo'shing:
#
#   ArrivedGroup ichiga (delivered_admin dan keyin):
#
#     cash_amount = models.DecimalField(
#         max_digits=12, decimal_places=2,
#         null=True, blank=True,
#         verbose_name="Naqd to'lov (so'm)"
#     )
#     card_amount = models.DecimalField(
#         max_digits=12, decimal_places=2,
#         null=True, blank=True,
#         verbose_name="Karta to'lov (so'm)"
#     )
#     delivered_at = models.DateTimeField(
#         null=True, blank=True,
#         verbose_name="Topshirilgan vaqt"
#     )
#
# ============================================================
# TO'LIQ YANGILANGAN warehouse/models.py:
# ============================================================

from django.db import models
from accounts.models import User


class ArrivedGroup(models.Model):
    STATUS_CHOICES = [
        ('To\'lov kutilmoqda', 'To\'lov kutilmoqda'),
        ('Tasdiqlash jarayonida', 'Tasdiqlash jarayonida'),
        ('To\'lov tasdiqlandi', 'To\'lov tasdiqlandi'),
        ('To\'lov rad etildi', 'To\'lov rad etildi'),
        ('Topshirildi', 'Topshirildi'),
    ]
    DELIVERY_METHODS = [
        ('Punktda', 'Punktda olib ketish'),
        ('Pochta', 'Pochta orqali'),
        ('Taksi', 'Taksi orqali'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='arrived_groups',
        verbose_name="Foydalanuvchi (UTS ID)"
    )
    receipt_code = models.CharField(max_length=50, verbose_name="Res kodi")
    total_weight = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name="Jami og'irlik (kg)"
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Jami summa (USD)"
    )
    image = models.ImageField(
        upload_to='arrived_groups/',
        verbose_name="Yuklar guruhi rasmi",
        null=True, blank=True  # ← null qo'shildi (eski: blank yo'q edi)
    )
    selected_cargos = models.ManyToManyField(
        'cargo.Cargo', blank=True,
        related_name='selected_in_groups',
        verbose_name="Yuklarni tanlash"
    )
    payment_status = models.CharField(
        max_length=30, choices=STATUS_CHOICES,
        default='To\'lov kutilmoqda'
    )
    payment_check = models.ImageField(
        upload_to='checks/', null=True, blank=True
    )
    admin_note = models.TextField(null=True, blank=True)
    delivery_method = models.CharField(
        max_length=20, choices=DELIVERY_METHODS,
        null=True, blank=True
    )
    delivery_address = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ── YANGI FIELDLAR ──────────────────────────────
    cash_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name="Naqd to'lov (so'm)"
    )
    card_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name="Karta to'lov (so'm)"
    )
    delivered_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Topshirilgan vaqt"
    )
    # ────────────────────────────────────────────────

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_groups',
        verbose_name="Qabul qilgan admin"
    )
    delivered_admin = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='delivered_groups',
        verbose_name="Topshirgan admin"
    )

    def __str__(self):
        return f"{self.receipt_code} - {self.payment_status}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.pk:
            self.selected_cargos.all().update(
                status='Punktda', arrived_group=self
            )

    class Meta:
        verbose_name = "Punkitga qabul (Guruh)"
        verbose_name_plural = "Punkitga qabul"


class PaymentRequest(ArrivedGroup):
    class Meta:
        proxy = True
        verbose_name = "To'lov tekshiruvi"
        verbose_name_plural = "To'lov tekshiruvlari"


class DeliveryQueue(ArrivedGroup):
    class Meta:
        proxy = True
        verbose_name = "Yukni topshirish navbati"
        verbose_name_plural = "Yukni topshirish navbati"
