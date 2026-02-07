from rest_framework import serializers
from .models import Cargo, SupportMessage


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['id', 'track_code', 'status', 'created_at', 'delivered_at']


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_type = serializers.SerializerMethodField()

    class Meta:
        model = SupportMessage
        fields = ['id', 'message', 'image', 'is_from_admin', 'sender_type', 'timestamp_ms']

    def get_sender_type(self, obj):
        return "Admin" if obj.is_from_admin else "Client"