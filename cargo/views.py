from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cargo
from .serializers import CargoTrackListSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_cargos(request):
    cargos = Cargo.objects.filter(user=request.user).order_by('-created_at')
    serializer = CargoTrackListSerializer(cargos, many=True)
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