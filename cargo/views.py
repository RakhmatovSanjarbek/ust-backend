from .models import Cargo
from .serializers import CargoSerializer

from rest_framework import status
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
