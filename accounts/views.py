import random
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, OTPCode
from .serializers import UserSerializer, UserUpdateSerializer


# 1. Tizimga kirish (OTP kod yaratish)
@api_view(['POST'])
@permission_classes([AllowAny])
def signin_request(request):
    phone = request.data.get('phone')
    if not phone:
        return Response({"message": "Telefon raqam kiritilmadi"}, status=status.HTTP_400_BAD_REQUEST)

    # Telefon raqamni tozalash
    phone = "".join(filter(str.isdigit, str(phone)))

    # Bazadan foydalanuvchini oxirgi 9 ta raqami bo'yicha qidirish
    user = User.objects.filter(phone__icontains=phone[-9:]).first()

    if user:
        # 6 xonali tasodifiy OTP kod yaratish
        otp_code = str(random.randint(100000, 999999))

        # OTPCode modeliga saqlash
        OTPCode.objects.create(user=user, code=otp_code)


        return Response({
            "message": "Tasdiqlash kodi yuborildi.",
        }, status=status.HTTP_200_OK)

    return Response({
        "message": "Bu raqam bazada mavjud emas. Avval ro'yxatdan o'ting."
    }, status=status.HTTP_404_NOT_FOUND)


# 2. OTP kodni tekshirish (Verify)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get('phone', None)
    otp_code = request.data.get('otp_code', None)

    if not phone or not otp_code:
        return Response({"message": "Telefon yoki kod kiritilmadi"}, status=400)

    phone = "".join(filter(str.isdigit, str(phone)))

    # Oxirgi kodni tekshirish
    otp_record = OTPCode.objects.filter(
        user__phone__icontains=phone[-9:],
        code=str(otp_code).strip()
    ).order_by('-created_at').first()

    if otp_record:
        user = otp_record.user
        user.is_active = True
        user.is_verified = True
        user.save()

        # Kodni o'chirish
        OTPCode.objects.filter(user=user).delete()

        # Faqat Access Token yaratish
        access_token = str(RefreshToken.for_user(user).access_token)

        return Response({
            "message": "Muvaffaqiyatli kirdingiz",
            "token": access_token
        }, status=200)

    return Response({"message": "Kod noto'g'ri yoki muddati o'tgan"}, status=400)
# 3. Ro'yxatdan o'tish (Signup)
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        # Foydalanuvchini yaratamiz lekin is_active=False qilamiz
        user = serializer.save(is_active=False)

        # OTP yaratish
        otp_code = str(random.randint(100000, 999999))
        OTPCode.objects.create(user=user, code=otp_code)

        return Response({
            "message": "Kod yuborildi. Tasdiqlagandan so'ng hisobingiz faollashadi.",
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# 4. Foydalanuvchi ma'lumotlarini olish (Me)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# 5. Profilni yangilash
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    user = request.user
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)