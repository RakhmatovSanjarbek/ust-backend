from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import UnassignedCargo
from .serializers import UnassignedCargoSerializer


class UnassignedCargoPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET'])
@permission_classes([AllowAny])
def unassigned_cargo_list(request):
    """
    Kodsiz tovarlar ro'yxati — pagination + search
    GET /api/unassigned/
    Query params:
      - search: trek kodi yoki reys raqami bo'yicha
      - page: sahifa raqami
    """
    cargos = UnassignedCargo.objects.all()

    search = request.query_params.get('search', '').strip()
    if search:
        from django.db.models import Q
        cargos = cargos.filter(
            Q(track_code__icontains=search) |
            Q(flight_name__icontains=search)
        )

    paginator = UnassignedCargoPagination()
    page = paginator.paginate_queryset(cargos, request)
    serializer = UnassignedCargoSerializer(page, many=True)

    return paginator.get_paginated_response(serializer.data)