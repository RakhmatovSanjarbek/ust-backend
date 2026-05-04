from rest_framework import serializers
from .models import User, UserRelative
import re

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
            'passport_front', 'passport_back', 'status', 'status_display', 'rejection_reason', 'rejection_reason_display',
            'rejection_note'
        ]
        read_only_fields = ['user_id', 'status']

    def validate_phone(self, value):
        phone = "".join(filter(str.isdigit, value))
        # Agar yangi user bo'lsa va raqam band bo'lsa xato beradi
        # Lekin 'rejected' bo'lgan user o'z ma'lumotlarini yangilayotganda bu tekshiruvdan o'tishi kerak
        user_exists = User.objects.filter(phone__icontains=phone[-9:]).exclude(status='rejected').exists()
        if not self.instance and user_exists:
            raise serializers.ValidationError("Bu telefon raqami allaqachon ro'yxatdan o'tgan.")
        return phone

    def validate_jshshir(self, value):
        if value:
            # JSHSHIR faqat tasdiqlangan yoki kutilayotganlarda takrorlanmasligi kerak
            qs = User.objects.filter(jshshir=value).exclude(status='rejected')
            if not self.instance and qs.exists():
                raise serializers.ValidationError("Ushbu JSHSHIR bazada mavjud.")
        return value