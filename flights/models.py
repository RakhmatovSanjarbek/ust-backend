from django.db import models


class Flight(models.Model):
    STATUS_CHOICES = [
        ('jarayonda', 'Jarayonda'),
        ('tranzit', 'Tranzit zonasida'),
        ('yetkazildi', 'Yetkazildi'),
    ]

    name = models.CharField(max_length=50, unique=True, verbose_name="Reys nomi")
    warehouse_start = models.DateField(verbose_name="Ombor qabul boshi")
    warehouse_end = models.DateField(verbose_name="Ombor qabul oxiri")
    arrival_date = models.DateField(verbose_name="Yetib kelish sanasi")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='jarayonda',
        verbose_name="Holati"
    )
    note = models.TextField(null=True, blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reys"
        verbose_name_plural = "Reyslar"
        ordering = ['-arrival_date']

    def __str__(self):
        return f"{self.name} | {self.get_status_display()}"