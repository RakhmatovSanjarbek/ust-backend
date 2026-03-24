import random
from datetime import timedelta
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from utils.sms_service import send_sms
from .models import User, OTPCode, UserRelative
from .serializers import UserSerializer, UserRelativeSerializer


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

    phone = normalize_phone(request.data.get("phone"))

    if not phone:
        return Response({"message": "Telefon raqam kiritilmadi"}, status=400)

    user = User.objects.filter(phone__icontains=phone[-9:]).first()

    if not user:
        return Response(
            {"message": "Bu raqam bazada mavjud emas. Avval ro'yxatdan o'ting."},
            status=404,
        )

    # eski OTP ni o'chiramiz
    OTPCode.objects.filter(user=user).delete()

    otp_code = generate_otp()

    OTPCode.objects.create(user=user, code=otp_code)

    # SMS yuborish
    send_sms(phone, f"UTS ilovasiga kirish uchun tasdiqlash kodi: {otp_code}")

    return Response({"message": "Tasdiqlash kodi SMS orqali yuborildi"})


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):

    phone = normalize_phone(request.data.get("phone"))
    otp_code = request.data.get("otp_code")

    if not phone or not otp_code:
        return Response({"message": "Telefon yoki kod kiritilmadi"}, status=400)

    otp_record = OTPCode.objects.filter(
        user__phone__icontains=phone[-9:], code=otp_code
    ).order_by("-created_at").first()

    if not otp_record:
        return Response({"message": "Kod noto'g'ri"}, status=400)

    # OTP 2 minut amal qiladi
    if otp_record.created_at < timezone.now() - timedelta(minutes=2):
        return Response({"message": "Kod muddati tugagan"}, status=400)

    user = otp_record.user

    user.is_active = True
    user.is_verified = True
    user.save()

    OTPCode.objects.filter(user=user).delete()

    token = str(RefreshToken.for_user(user).access_token)

    return Response(
        {
            "message": "Muvaffaqiyatli kirdingiz",
            "token": token,
        },
        status=200,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):

    serializer = UserSerializer(data=request.data)

    if not serializer.is_valid():
        error_message = " ".join([e[0] for e in serializer.errors.values()])
        return Response({"message": error_message}, status=400)

    user = serializer.save(is_active=False)

    phone = normalize_phone(user.phone)

    OTPCode.objects.filter(user=user).delete()

    otp_code = generate_otp()

    OTPCode.objects.create(user=user, code=otp_code)

    send_sms(phone, f"UTS ilovasiga kirish uchun tasdiqlash kodi: {otp_code}")

    return Response(
        {"message": "Ro'yxatdan o'tish muvaffaqiyatli. SMS yuborildi"},
        status=200,
    )

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
@permission_classes([IsAuthenticated])
def get_user_data(request):

    serializer = UserSerializer(request.user)

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