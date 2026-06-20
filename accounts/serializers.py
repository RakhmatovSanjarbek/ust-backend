from rest_framework import serializers
from .models import User, UserRelative
import re
import os
import uuid


def _safe_image_field(file_obj):
    if file_obj is None:
        return None

    ALLOWED_MIME = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/webp',
        'image/heic', 'image/heif', 'application/octet-stream',
    }
    ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}

    content_type = getattr(file_obj, 'content_type', '') or ''
    name = getattr(file_obj, 'name', '') or ''
    ext = os.path.splitext(name)[1].lower()

    if content_type.lower() not in ALLOWED_MIME and ext not in ALLOWED_EXT:
        raise serializers.ValidationError("Faqat rasm fayllari qabul qilinadi (JPEG, PNG, WEBP, HEIC).")

    safe_name = f"{uuid.uuid4()}{ext if ext else '.jpg'}"
    file_obj.name = safe_name
    return file_obj


class UserRelativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRelative
        fields = ["id", "full_name", "jshshir", "passport_series", "birth_date", "phone", "created_at"]

    def validate_passport_series(self, value):
        if not re.match(r"^[A-Z]{2}\d{7}$", value.upper()):
            raise serializers.ValidationError("Pasport seriyasi noto'g'ri (AA1234567)")
        return value.upper()


class UserSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    rejection_reason_display = serializers.CharField(source='get_rejection_reason_display', read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "user_id", "phone", "first_name", "last_name",
            "jshshir", "passport_series", "birth_date", "address",
            'passport_front', 'passport_back', 'status', 'status_display',
            'rejection_reason', 'rejection_reason_display', 'rejection_note'
        ]
        read_only_fields = ['user_id', 'status']

    def validate_passport_front(self, value):
        return _safe_image_field(value)

    def validate_passport_back(self, value):
        return _safe_image_field(value)

    def validate_phone(self, value):
        phone = "".join(filter(str.isdigit, value))
        user_exists = User.objects.filter(phone__icontains=phone[-9:]).exclude(status='rejected').exists()
        if not self.instance and user_exists:
            raise serializers.ValidationError("Bu telefon raqami allaqachon ro'yxatdan o'tgan.")
        return phone

    def validate_jshshir(self, value):
        if value:
            qs = User.objects.filter(jshshir=value).exclude(status='rejected')
            if not self.instance and qs.exists():
                raise serializers.ValidationError("Ushbu JSHSHIR bazada mavjud.")
        return value