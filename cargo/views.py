from .models import Cargo, TutorialVideo, CalculationRequest
from .serializers import CargoSerializer, TutorialVideoSerializer, CalculationRequestSerializer

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import SupportMessage
from .serializers import SupportMessageSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_cargos(request):
    cargos = Cargo.objects.filter(user=request.user).order_by('-created_at')
    serializer = CargoSerializer(cargos, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_delivered(request):
    track_code = request.data.get('track_code')
    cargo = Cargo.objects.filter(track_code=track_code).first()

    if cargo:
        from django.utils import timezone
        cargo.status = 'Topshirildi'
        cargo.delivered_at = timezone.now()
        cargo.save()
        return Response({"message": f"{track_code} yuk topshirildi deb belgilandi"})

    return Response({"error": "Yuk topilmadi"}, status=404)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def support_chat_view(request):
    user = request.user

    if request.method == 'GET':
        messages = SupportMessage.objects.filter(user=user)
        serializer = SupportMessageSerializer(messages, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = SupportMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user, is_from_admin=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VideoListView(generics.ListAPIView):
    queryset = TutorialVideo.objects.all().order_by('-created_at')
    serializer_class = TutorialVideoSerializer
    permission_classes = [permissions.AllowAny]

class CalculationCreateListView(generics.ListCreateAPIView):
    serializer_class = CalculationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get_queryset(self): return CalculationRequest.objects.filter(user=self.request.user).order_by('-created_at')
    def perform_create(self, serializer): serializer.save(user=self.request.user)