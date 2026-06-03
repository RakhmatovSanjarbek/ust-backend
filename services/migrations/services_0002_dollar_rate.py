"""
services/migrations/0004_warehousesettings_dollar_rate.py
----------------------------------------------------------
WarehouseSettings.dollar_rate  — kunlik dollar kursi (so'm)
WarehouseSettings.dollar_rate_updated_at — oxirgi yangilangan vaqt
"""
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0003_appversion'),
    ]

    operations = [
        migrations.AddField(
            model_name='warehousesettings',
            name='dollar_rate',
            field=models.DecimalField(
                blank=True, decimal_places=2, default=12700,
                max_digits=10, verbose_name="Dollar kursi (so'm)"
            ),
        ),
        migrations.AddField(
            model_name='warehousesettings',
            name='dollar_rate_updated_at',
            field=models.DateTimeField(
                blank=True, null=True,
                verbose_name="Kurs oxirgi yangilangan vaqt"
            ),
        ),
    ]
