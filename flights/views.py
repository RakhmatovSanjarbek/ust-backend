from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Flight
from .serializers import FlightSerializer


class FlightPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET'])
@permission_classes([AllowAny])
def flight_list(request):
    """
    Reyslar ro'yxati — ochiq API
    GET /api/flights/
    Query params:
      - status: jarayonda | tranzit | yetkazildi
      - page: sahifa raqami
    """
    flights = Flight.objects.all()

    status = request.query_params.get('status', '').strip()
    if status:
        flights = flights.filter(status=status)

    paginator = FlightPagination()
    page = paginator.paginate_queryset(flights, request)
    serializer = FlightSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)