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
    class Meta:
        model = User
        fields = [
            "id",
            "user_id",
            "phone",
            "first_name",
            "last_name",
            "jshshir",
            "passport_series",
            "birth_date",
            "address",
        ]

    def validate_phone(self, value):
        phone = "".join(filter(str.isdigit, value))

        if len(phone) < 9:
            raise serializers.ValidationError(
                "Telefon raqami kamida 9 ta raqamdan iborat bo'lishi kerak."
            )

        if User.objects.filter(phone__icontains=phone[-9:]).exists():
            raise serializers.ValidationError(
                "Bu telefon raqami allaqachon ro'yxatdan o'tgan."
            )

        return phone

    def validate_jshshir(self, value):
        if not value.isdigit() or len(value) != 14:
            raise serializers.ValidationError(
                "JSHSHIR 14 ta raqamdan iborat bo'lishi kerak."
            )

        if User.objects.filter(jshshir=value).exists():
            raise serializers.ValidationError("Ushbu JSHSHIR bazada mavjud.")

        return value

    def validate_passport_series(self, value):
        if not re.match(r"^[A-Z]{2}\d{7}$", value.upper()):
            raise serializers.ValidationError(
                "Pasport seriyasi noto'g'ri formatda (AA1234567)"
            )

        return value.upper()