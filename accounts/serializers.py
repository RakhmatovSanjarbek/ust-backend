from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'user_id',
            'phone',
            'first_name',
            'last_name',
            'jshshir',
            'passport_series',
            'birth_date',
        ]
        # user_id va is_verified faqat server tomonidan boshqariladi
        read_only_fields = ['user_id']

    def validate_phone(self, value):
        """Telefon raqami faqat raqamlardan iboratligini tekshirish"""
        clean_phone = "".join(filter(str.isdigit, str(value)))
        if len(clean_phone) < 9:
            raise serializers.ValidationError("Telefon raqami noto'g'ri formatda.")
        return value

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'jshshir',
            'passport_series',
            'birth_date'
        ]