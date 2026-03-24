from rest_framework import serializers
from .models import Cargo

class CargoTrackListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['id', 'track_code', 'flight_name', 'status', 'created_at', 'updated_at', 'delivered_at']