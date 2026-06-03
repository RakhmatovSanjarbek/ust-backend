from rest_framework import serializers
from cargo.serializers import CargoTrackListSerializer
from warehouse.models import ArrivedGroup


class ArrivedGroupListSerializer(serializers.ModelSerializer):
    cargos = CargoTrackListSerializer(many=True, read_only=True)

    class Meta:
        model = ArrivedGroup
        fields = [
            'id', 'receipt_code', 'total_price', 'total_weight', 'image',
            'payment_status', 'payment_check', 'delivery_method',
            'delivery_address', 'created_at', 'cargos', 'admin_note'
        ]

class AdminArrivedGroupSerializer(serializers.ModelSerializer):
    user_details = serializers.CharField(source='user.first_name', read_only=True)
    uts_id = serializers.CharField(source='user.user_id', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    cargos_count = serializers.IntegerField(source='cargos.count', read_only=True)

    class Meta:
        model = ArrivedGroup
        fields = [
            'id', 'uts_id', 'user_details', 'phone', 'receipt_code',
            'total_price', 'payment_status', 'payment_check',
            'cargos_count', 'created_at'
        ]