"""
warehouse/migrations/0002_arrivedgroup_payment_fields.py
---------------------------------------------------------
Qo'shilayotgan fieldlar:
  ArrivedGroup.cash_amount  — naqd to'lov miqdori (so'm)
  ArrivedGroup.card_amount  — karta to'lov miqdori (so'm)
  ArrivedGroup.delivered_at — topshirilgan vaqt
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrivedgroup',
            name='cash_amount',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12,
                null=True, verbose_name="Naqd to'lov (so'm)"
            ),
        ),
        migrations.AddField(
            model_name='arrivedgroup',
            name='card_amount',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12,
                null=True, verbose_name="Karta to'lov (so'm)"
            ),
        ),
        migrations.AddField(
            model_name='arrivedgroup',
            name='delivered_at',
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Topshirilgan vaqt"
            ),
        ),
    ]
