from rest_framework import status 
from rest_framework.response import Response 
from rest_framework.decorators import api_view, permission_classes 
from rest_framework.request import Request 
from rest_framework.permissions import IsAuthenticated
from .custums import JWT 
from .models import Notifications
from .serializers import NotificationsSerializer
from django.db.models import Q 
from drf_spectacular.utils import extend_schema
from django.db.models import Q
import time 
from django.http import StreamingHttpResponse 




@extend_schema(
     tags=['Notifications'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_notification(request:Request , *args, **kwargs):
    _ ,  user  = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    notifications = Notifications.objects.filter(Q(sender=user) | Q(recipient=user))
    
    serializer = NotificationsSerializer(notifications, many=True)
    content = {"Messages":"All Notifications", "Data":serializer.data}
    return Response(data=content, status=status.HTTP_200_OK)



@extend_schema(
     tags=['Notifications'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtain_notifications(request:Request ,notification_id :str , *args, **kwargs) : 
    try : 
        notifications = Notifications.objects.get(id=notification_id)
        
        serializer = NotificationsSerializer(notifications)
        content = {"Messages":"All Notifications", "Data":serializer.data}
    
        return Response(data=content, status=status.HTTP_200_OK)
        
    except Notifications.DoesNotExist : 
        content = {"Message":"Notification  Does not Exist"}
        return Response( status=status.HTTP_404_NOT_FOUND)
    


   
@extend_schema(
     tags=['Notifications'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request:Request , notification_id:str, *args, **kwargs) : 
    _ ,  user  = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    try:
        notification = Notifications.objects.get(id=notification_id)
        notification.mark_as_read()
        
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
    except Notifications.DoesNotExist:
        return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=['Notifications'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'notification_ids': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of notification IDs to delete'
                }
            },
            'required': ['notification_ids']
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'deleted_count': {'type': 'integer'},
                'failed_ids': {'type': 'array', 'items': {'type': 'string'}}
            }
        }
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def bulk_delete_notifications(request: Request, *args, **kwargs):
    """
    Bulk delete notifications. Accepts a list of notification IDs.
    Only deletes notifications where the authenticated user is the recipient.
    """
    _ , user = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    notification_ids = request.data.get('notification_ids', [])
    
    if not notification_ids:
        return Response(
            {"error": "notification_ids is required and must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not isinstance(notification_ids, list):
        return Response(
            {"error": "notification_ids must be a list."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Filter notifications that belong to the authenticated user (as recipient)
    notifications_to_delete = Notifications.objects.filter(
        id__in=notification_ids,
        recipient=user
    )
    
    # Get the IDs that were actually found
    found_ids = set(notifications_to_delete.values_list('id', flat=True))
    requested_ids = set(notification_ids)
    failed_ids = list(requested_ids - found_ids)
    
    # Delete the notifications
    deleted_count, _ = notifications_to_delete.delete()
    
    return Response({
        "message": f"Successfully deleted {deleted_count} notification(s).",
        "deleted_count": deleted_count,
        "failed_ids": failed_ids
    }, status=status.HTTP_200_OK)