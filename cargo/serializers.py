from rest_framework import serializers

from accounts.models import User
from .models import Cargo, SupportMessage


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ['id', 'track_code', 'status', 'created_at', 'delivered_at']


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_type = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,  # user maydoni majburiy emas
        allow_null=True  # null qiymatga ruxsat berish
    )

    class Meta:
        model = SupportMessage
        fields = ['id', 'user', 'message', 'image', 'is_from_admin', 'sender_type', 'timestamp_ms']
        extra_kwargs = {
            'user': {'required': False, 'allow_null': True}
        }

    def get_sender_type(self, obj):
        return "Admin" if obj.is_from_admin else "Client"

    def create(self, validated_data):
        # Agar user berilmagan bo'lsa, requestdan olish
        request = self.context.get('request')
        if request and request.user and not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)