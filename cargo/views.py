from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Cargo
from .serializers import CargoTrackListSerializer


class CargoPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_cargos(request):
    """
    Foydalanuvchining yuklarini olish.
    Query params:
      - search: trek kodi yoki reys nomi bo'yicha qidirish
      - status: Omborda | Yo'lda | Punktda | Topshirildi | Kutilmoqda
      - page: sahifa raqami (default: 1)
    """
    cargos = Cargo.objects.filter(user=request.user).order_by('-created_at')

    # Status filter
    status = request.query_params.get('status', '').strip()
    if status and status != 'Barchasi':
        cargos = cargos.filter(status=status)

    # Search filter
    search = request.query_params.get('search', '').strip()
    if search:
        cargos = cargos.filter(track_code__icontains=search)

    paginator = CargoPagination()
    page = paginator.paginate_queryset(cargos, request)
    serializer = CargoTrackListSerializer(page, many=True)

    return paginator.get_paginated_response(serializer.data)


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