import random
from datetime import timedelta
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from utils.sms_service import send_sms
from .models import User, OTPCode, UserRelative
from .serializers import UserSerializer, UserRelativeSerializer

from rest_framework.parsers import MultiPartParser, FormParser


def generate_otp():
    return str(random.randint(100000, 999999))


def normalize_phone(phone):

    phone = "".join(filter(str.isdigit, str(phone)))

    if phone.startswith("998") and len(phone) == 12:
        return phone

    if len(phone) == 9:
        return "998" + phone

    if len(phone) == 12 and not phone.startswith("998"):
        return "998" + phone[-9:]

    if len(phone) == 11:
        return "998" + phone[-9:]

    return phone


@api_view(["POST"])
@permission_classes([AllowAny])
def signin_request(request):
    # Raqamni normallashtiramiz
    phone_input = request.data.get("phone")
    phone = normalize_phone(phone_input)

    if not phone:
        return Response({"message": "Telefon raqam kiritilmadi"}, status=400)

    # --- GOOGLE TESTER UCHUN MAXSUS YO'L (BOSHIGA QO'SHILDI) ---
    if phone == "998940000000":
        # Bu usul foydalanuvchi bo'lsa ma'lumotlarini yangilaydi, bo'lmasa yaratadi
        user, created = User.objects.get_or_create(phone="998940000000")

        user.first_name = "Google"
        user.last_name = "Tester"
        user.jshshir = "12345678901234"
        user.passport_series = "AA1234567"
        user.birth_date = "1990-01-01"
        user.address = "Toshkent sh., Amir Temur ko'chasi, 10-uy"
        user.user_id = "UTS-999"  # Majburiy UTS-999 qilamiz
        user.is_active = True
        user.is_verified = True

        # Agar foydalanuvchi yangi bo'lsa, parolini sozlaymiz
        if created:
            user.set_unusable_password()

        user.save()

        # OTP yaratish
        OTPCode.objects.filter(user=user).delete()
        OTPCode.objects.create(user=user, code="123456")

        return Response({"message": "Test rejimida kod yuborildi (123456)"})

    # --- GOOGLE TESTER TUGADI ---

    # ODDIY FOYDALANUVCHILAR UCHUN ASLIY MANTIQ
    user = User.objects.filter(phone__icontains=phone[-9:]).first()

    if not user:
        return Response(
            {"message": "Bu raqam bazada mavjud emas. Avval ro'yxatdan o'ting."},
            status=404,
        )

    # Eski OTP ni o'chiramiz
    OTPCode.objects.filter(user=user).delete()

    # Yangi tasodifiy OTP yaratamiz
    otp_code = generate_otp()
    OTPCode.objects.create(user=user, code=otp_code)

    # Haqiqiy SMS yuborish
    send_sms(phone, f"UTS ilovasiga kirish uchun tasdiqlash kodi: {otp_code}")

    return Response({"message": "Tasdiqlash kodi SMS orqali yuborildi"})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    phone_input = request.data.get("phone")
    phone = normalize_phone(phone_input)
    otp_code = request.data.get("otp_code")

    if not phone or not otp_code:
        return Response({"message": "Telefon yoki kod kiritilmadi"}, status=400)

    # Oxirgi yuborilgan kodni olish
    otp_record = OTPCode.objects.filter(
        user__phone__icontains=phone[-9:],
        code=otp_code
    ).order_by("-created_at").first()

    if not otp_record:
        return Response({"message": "Tasdiqlash kodi noto'g'ri"}, status=400)

    # 2 minutlik muddatni tekshirish
    if otp_record.created_at < timezone.now() - timedelta(minutes=2):
        return Response({"message": "Kod muddati tugagan. Qaytadan so'rang."}, status=400)

    user = otp_record.user

    # Foydalanuvchini tasdiqlangan (verified) deb belgilaymiz
    user.is_verified = True
    user.last_active = timezone.now()  # Aktivlik vaqtini yangilash
    user.save()

    # Ishlatilgan kodni o'chiramiz
    OTPCode.objects.filter(user=user).delete()

    # JWT Tokenlarni generatsiya qilish
    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "message": "Muvaffaqiyatli kirdingiz",
            "token": str(refresh.access_token),  # Faqat bitta asosiy token
        },
        status=200,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def signup(request):
    phone = normalize_phone(request.data.get("phone"))
    user = User.objects.filter(phone__icontains=phone[-9:]).first()

    if user:
        if user.status == 'approved':
            return Response({"message": "Allaqachon tasdiqlangan"}, status=400)
        serializer = UserSerializer(user, data=request.data, partial=True)
    else:
        serializer = UserSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        user.is_active = True  # MUKAMMAL YECHIM: Token ishlashi uchun
        user.status = 'pending'
        user.save()

        OTPCode.objects.filter(user=user).delete()
        otp_code = generate_otp()
        OTPCode.objects.create(user=user, code=otp_code)
        send_sms(phone, f"Tasdiqlash kodi: {otp_code}")
        return Response({"message": "SMS yuborildi, arizangiz kutilmoqda"}, status=200)

    return Response(serializer.errors, status=400)

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def manage_relatives(request):
    if request.method == "GET":
        relatives = request.user.relatives.all()
        serializer = UserRelativeSerializer(relatives, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = UserRelativeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_relative(request, pk):
    try:
        relative = request.user.relatives.get(pk=pk)
        relative.delete()
        return Response({"message": "Muvaffaqqiyatli o'chirildi"}, status=204)
    except UserRelative.DoesNotExist:
        return Response({"message": "Topilmadi"}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated]) # Endi bu muammosiz ishlaydi
def get_user_data(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_user_profile(request):

    serializer = UserSerializer(request.user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):

    user = request.user

    active_cargos = user.cargos.exclude(status="Topshirildi").exists()

    if active_cargos:
        return Response(
            {
                "message": "Sizda hali topshirilmagan yuklar mavjud."
            },
            status=400,
        )

    user.delete()

    return Response(
        {"message": "Hisob muvaffaqiyatli o'chirildi"},
        status=204,
    )