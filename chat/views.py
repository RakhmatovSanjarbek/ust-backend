from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ChatMessage

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_messages(request):
    messages = ChatMessage.objects.filter(user=request.user).order_by('created_at')
    data = [{
        'id': msg.id,
        'message': msg.message,
        'image': msg.image.url if msg.image else None,
        'is_from_admin': msg.is_from_admin,
        'created_at': msg.created_at.isoformat(),
        'time': msg.created_at.strftime('%H:%M'),
        'date': msg.created_at.strftime('%d.%m.%Y')
    } for msg in messages]
    return Response({'status': 'success', 'messages': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def send_user_message(request):
    message = request.data.get('message', '')
    image = request.FILES.get('image')
    if not message and not image:
        return Response({'status': 'error', 'message': 'Xabar yoki rasm kerak'}, status=400)
    chat_msg = ChatMessage.objects.create(
        user=request.user,
        message=message,
        image=image,
        is_from_admin=False,
        is_read=False
    )
    return Response({'status': 'success', 'message': 'Xabar yuborildi'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    unread_count = ChatMessage.objects.filter(user=request.user, is_from_admin=True, is_read=False).count()
    return Response({'status': 'success', 'unread_count': unread_count})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request):
    updated = ChatMessage.objects.filter(user=request.user, is_from_admin=True, is_read=False).update(is_read=True)
    return Response({'status': 'success', 'marked_count': updated})