from rest_framework import serializers
from .models import Flight


class FlightSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    warehouse_period = serializers.SerializerMethodField()

    class Meta:
        model = Flight
        fields = [
            'id', 'name', 'warehouse_start', 'warehouse_end',
            'warehouse_period', 'arrival_date', 'status',
            'status_display', 'note'
        ]

    def get_warehouse_period(self, obj):
        start = obj.warehouse_start.strftime('%d.%m')
        end = obj.warehouse_end.strftime('%d.%m')
        return f"{start} - {end}"
