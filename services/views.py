from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import SupportMessage, TutorialVideo, CalculationRequest, WarehouseSettings
from .serializers import SupportMessageSerializer, TutorialVideoSerializer, CalculationRequestSerializer, \
    WarehouseSettingsSerializer


# --- SUPPORT CHAT VIEW ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def support_chat_view(request):
    user = request.user

    if request.method == 'GET':
        # Faqat joriy foydalanuvchiga tegishli xabarlarni qaytaramiz
        messages = SupportMessage.objects.filter(user=user).order_by('created_at')
        serializer = SupportMessageSerializer(messages, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Yangi xabar yuborish
        serializer = SupportMessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Mijoz yuborgani uchun is_from_admin doim False bo'ladi
            serializer.save(user=user, is_from_admin=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Hamma ko'ra olishi uchun
def get_warehouse_info(request):
    settings = WarehouseSettings.objects.last()
    if not settings:
        return Response({"error": "Ma'lumotlar topilmadi"}, status=404)

    serializer = WarehouseSettingsSerializer(settings)
    return Response(serializer.data)


# --- TUTORIAL VIDEOS VIEW ---
class VideoListView(generics.ListAPIView):
    queryset = TutorialVideo.objects.all().order_by('-created_at')
    serializer_class = TutorialVideoSerializer
    # Videolarni hamma ko'ra olishi mumkin
    permission_classes = [permissions.AllowAny]


# --- CALCULATION REQUEST VIEW ---
class CalculationCreateListView(generics.ListCreateAPIView):
    serializer_class = CalculationRequestSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Mijoz faqat o'zining narx hisoblash so'rovlarini ko'radi
        return CalculationRequest.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # So'rovni saqlayotganda joriy foydalanuvchini biriktiramiz
        serializer.save(user=self.request.user)
