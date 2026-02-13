from rest_framework import serializers

from accounts.models import User
from .models import Cargo, SupportMessage, TutorialVideo, CalculationRequest


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['id', 'track_code', 'status', 'created_at', 'delivered_at']


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_type = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = SupportMessage
        fields = ['id', 'user', 'message', 'image', 'is_from_admin', 'sender_type', 'timestamp_ms']
        extra_kwargs = {
            'user': {'required': False, 'allow_null': True}
        }

    @staticmethod
    def get_sender_type(obj):
        return "Admin" if obj.is_from_admin else "Client"

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)

class TutorialVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TutorialVideo
        fields = ['id', 'video_url', 'created_at']

class CalculationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculationRequest
        fields = ['id', 'image', 'weight', 'length', 'width', 'height', 'comment', 'price', 'admin_note', 'is_responded', 'created_at']
        read_only_fields = ['price', 'admin_note', 'is_responded']