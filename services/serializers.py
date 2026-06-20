import os
import uuid
from rest_framework import serializers
from accounts.models import User
from .models import SupportMessage, TutorialVideo, CalculationRequest, WarehouseSettings, AppVersion

ALLOWED_MIME = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/webp',
    'image/heic', 'image/heif', 'application/octet-stream',
}
ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}


def _safe_image(file_obj):
    if file_obj is None:
        return None
    content_type = (getattr(file_obj, 'content_type', '') or '').lower()
    name = getattr(file_obj, 'name', '') or ''
    ext = os.path.splitext(name)[1].lower()
    if content_type not in ALLOWED_MIME and ext not in ALLOWED_EXT:
        raise serializers.ValidationError("Faqat rasm fayllari qabul qilinadi.")
    file_obj.name = f"{uuid.uuid4()}{ext if ext else '.jpg'}"
    return file_obj


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_type = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = SupportMessage
        fields = ['id', 'user', 'message', 'image', 'is_from_admin', 'sender_type', 'timestamp_ms']
        extra_kwargs = {'user': {'required': False, 'allow_null': True}}

    @staticmethod
    def get_sender_type(obj):
        return "Admin" if obj.is_from_admin else "Client"

    def validate_image(self, value):
        return _safe_image(value)

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
        fields = [
            'id', 'image', 'weight', 'length', 'width', 'height',
            'comment', 'price', 'admin_note', 'is_responded', 'created_at'
        ]
        read_only_fields = ['price', 'admin_note', 'is_responded']

    def validate_image(self, value):
        return _safe_image(value)


class WarehouseSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseSettings
        fields = '__all__'

    def to_representation(self, instance):
        return {
            "Xitoy_AVIA": {
                "phone": instance.china_avia_phone,
                "address": instance.china_avia_address,
                "price": instance.china_avia_price,
                "term": instance.china_avia_term,
            },
            "Xitoy_AVTO": {
                "phone": instance.china_auto_phone,
                "address": instance.china_auto_address,
                "price": instance.china_auto_price,
                "term": instance.china_auto_term,
            },
            "contact": {
                "telegram": instance.contact_telegram,
                "instagram": instance.contact_instagram,
                "phone": instance.contact_phone,
            },
            "dollar_rate": instance.dollar_rate,
            "payment_card": {
                "number": instance.payment_card_number,
                "holder": instance.payment_card_holder,
            },
            "pickup": {
                "name": instance.pickup_name,
                "lat": instance.pickup_lat,
                "lng": instance.pickup_lng,
            },
        }


class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = ['version', 'play_store_url', 'app_store_url', 'is_force_update']