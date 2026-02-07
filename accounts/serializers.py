from rest_framework import serializers
from .models import User
import re

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'user_id', 'phone', 'first_name', 'last_name',
            'jshshir', 'passport_series', 'birth_date'
        ]
        # Barcha maydonlar majburiy bo'lishi uchun:
        extra_kwargs = {
            'phone': {'required': True, 'error_messages': {"required": "Telefon raqam kiritilishi shart."}},
            'first_name': {'required': True, 'error_messages': {"required": "Ism kiritilishi shart."}},
            'last_name': {'required': True, 'error_messages': {"required": "Familiya kiritilishi shart."}},
            'jshshir': {'required': True, 'error_messages': {"required": "JSHSHIR kiritilishi shart."}},
            'passport_series': {'required': True, 'error_messages': {"required": "Pasport seriyasi kiritilishi shart."}},
            'birth_date': {'required': True, 'error_messages': {"required": "Tug'ilgan sana kiritilishi shart."}},
        }

    def validate_phone(self, value):
        clean_phone = "".join(filter(str.isdigit, str(value)))
        if len(clean_phone) < 9:
            raise serializers.ValidationError("Telefon raqami kamida 9 ta raqamdan iborat bo'lishi kerak.")
        if User.objects.filter(phone__icontains=clean_phone[-9:]).exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ro'yxatdan o'tgan.")
        return value

    def validate_jshshir(self, value):
        if not value.isdigit() or len(value) != 14:
            raise serializers.ValidationError("JSHSHIR 14 ta raqamdan iborat bo'lishi kerak.")
        if User.objects.filter(jshshir=value).exists():
            raise serializers.ValidationError("Ushbu JSHSHIR bazada mavjud.")
        return value

    def validate_passport_series(self, value):
        # Format: AA1234567
        if not re.match(r'^[A-Z]{2}\d{7}$', value.upper()):
            raise serializers.ValidationError("Pasport seriyasi noto'g'ri formatda (Masalan: AA1234567).")
        return value.upper()