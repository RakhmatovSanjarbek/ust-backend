from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Notification
from .serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Foydalanuvchining barcha bildirishnomalarini olish (pagination bilan)
    GET /api/notifications/
    """
    notifications = Notification.objects.filter(user=request.user)

    paginator = NotificationPagination()
    page = paginator.paginate_queryset(notifications, request)
    serializer = NotificationSerializer(page, many=True)

    return paginator.get_paginated_response({
        'results': serializer.data,
        'unread_count': notifications.filter(is_read=False).count()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_read(request, notification_id):
    """
    Bitta bildirishnomani o'qilgan deb belgilash
    POST /api/notifications/<id>/read/
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'message': 'O\'qildi'})
    except Notification.DoesNotExist:
        return Response({'error': 'Topilmadi'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    """
    Barcha bildirishnomalarni o'qilgan deb belgilash
    POST /api/notifications/read-all/
    """
    count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'message': f'{count} ta bildirishnoma o\'qildi'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    """
    O'qilmagan bildirishnomalar soni
    GET /api/notifications/unread-count/
    """
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'unread_count': count})