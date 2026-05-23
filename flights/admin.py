from django.contrib import admin
from django.utils.html import format_html
from .models import Flight


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'warehouse_period', 'arrival_date',
        'colored_status', 'note'
    )
    list_filter = ('status',)
    search_fields = ('name',)
    list_per_page = 30
    ordering = ('-arrival_date',)

    fieldsets = (
        ('Reys ma\'lumotlari', {
            'fields': ('name', 'status')
        }),
        ('Sanalar', {
            'fields': ('warehouse_start', 'warehouse_end', 'arrival_date')
        }),
        ('Qo\'shimcha', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
    )

    def warehouse_period(self, obj):
        return format_html(
            '📦 {}&nbsp;–&nbsp;{}',
            obj.warehouse_start.strftime('%d.%m'),
            obj.warehouse_end.strftime('%d.%m'),
        )
    warehouse_period.short_description = "Xitoy ombor sanasi"

    def colored_status(self, obj):
        colors = {
            'jarayonda': ('#f59e0b', '#fffbeb', '⏳'),
            'tranzit':   ('#3b82f6', '#eff6ff', '✈️'),
            'yetkazildi': ('#10b981', '#ecfdf5', '✅'),
        }
        color, bg, icon = colors.get(obj.status, ('#6b7280', '#f9fafb', '❓'))
        return format_html(
            '<span style="background:{};color:{};padding:4px 12px;'
            'border-radius:20px;font-weight:600;font-size:12px;">'
            '{} {}</span>',
            bg, color, icon, obj.get_status_display()
        )
    colored_status.short_description = "Holati"