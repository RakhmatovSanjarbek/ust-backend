from rest_framework import serializers
from .models import UnassignedCargo


class UnassignedCargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnassignedCargo
        fields = ['id', 'track_code', 'flight_name', 'created_at', 'note']