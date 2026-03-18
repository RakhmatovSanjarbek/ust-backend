from rest_framework import serializers
from accounts.models import User
from .models import SupportMessage, TutorialVideo, CalculationRequest, WarehouseSettings


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_type = serializers.SerializerMethodField()
    # Foydalanuvchini avtomatik aniqlash uchun PrimaryKeyRelatedField ishlatamiz
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
        # Agar xabar yuborilayotganda user berilmasa, request'dagi user'ni olamiz
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
                "term": instance.china_avia_term
            },
            "Xitoy_AVTO": {
                "phone": instance.china_auto_phone,
                "address": instance.china_auto_address,
                "price": instance.china_auto_price,
                "term": instance.china_auto_term
            },
            "contact": {
                "telegram": instance.contact_telegram,
                "instagram": instance.contact_instagram,
                "phone": instance.contact_phone
            }
        }