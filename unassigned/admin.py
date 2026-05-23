from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from django.utils import timezone
import datetime

from .models import UnassignedCargo


class UnassignedCargoResource(resources.ModelResource):
    track_code = Field(attribute='track_code', column_name='TREK RAQAM')
    flight_name = Field(attribute='flight_name', column_name='REYS')
    created_at = Field(attribute='created_at', column_name='SANA')
    note = Field(attribute='note', column_name='IZOH')

    class Meta:
        model = UnassignedCargo
        import_id_fields = ('track_code',)
        fields = ('track_code', 'flight_name', 'created_at', 'note')
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        track_code = row.get('TREK RAQAM', '')
        if track_code:
            row['TREK RAQAM'] = str(track_code).strip()

        flight_name = row.get('REYS', '')
        if flight_name:
            row['REYS'] = str(flight_name).strip()

        # ✅ Naive datetime ni timezone aware ga o'tkazamiz
        created_at = row.get('SANA', '')
        if created_at and str(created_at).strip() not in ['', 'None', 'null']:
            if isinstance(created_at, datetime.datetime):
                row['SANA'] = timezone.make_aware(created_at)
            elif isinstance(created_at, datetime.date):
                row['SANA'] = timezone.make_aware(
                    datetime.datetime.combine(created_at, datetime.time.min)
                )
        else:
            row['SANA'] = timezone.now()

        return True

    def after_import(self, dataset, result, **kwargs):
        # ✅ is_dry_run o'rniga using_transactions tekshiramiz
        new_count = sum(1 for r in result.rows if r.import_type == 'new')
        update_count = sum(1 for r in result.rows if r.import_type == 'update')
        if new_count > 0 or update_count > 0:
            print(f"""
    ╔══════════════════════════════════════════════╗
    ║         KODSIZ TOVARLAR IMPORT               ║
    ╠══════════════════════════════════════════════╣
    ║  ✅ Yangi: {new_count} ta
    ║  🔄 Yangilangan: {update_count} ta
    ╚══════════════════════════════════════════════╝
            """)


@admin.register(UnassignedCargo)
class UnassignedCargoAdmin(ImportExportModelAdmin):
    resource_class = UnassignedCargoResource

    list_display = ('track_code', 'flight_name', 'created_at', 'note')
    list_filter = ('flight_name', 'created_at')
    search_fields = ('track_code', 'flight_name')
    list_per_page = 30
    ordering = ('-created_at',)

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('track_code', 'flight_name', 'created_at')
        }),
        ('Qo\'shimcha', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
    )