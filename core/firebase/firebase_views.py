from rest_framework.decorators import api_view , permission_classes , parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema
from notifications.custums import JWT
from fcm_django.models import FCMDevice
from rest_framework import status


@extend_schema(
    tags=['FireBase Service'], 
    request={
        'application/json': {
            'properties': {
                'fcm_token': {'type': 'string', 'example': 'fcm_token'},
                'device_type': {'type': 'string', 'example': 'android or ios'}
            }
        }
    },
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_view(request:Request):
    """
        Registers a device for a user with the FCM token.
        Args: request: HTTP object containing the FCM token in POST. user: User for whom the device is registered.
        Returns: dict: Result of the registration process.
    """
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    fcm_token = request.data.get("fcm_token")

        
    if not fcm_token:
        return {"error": "FCM token is required."}
    try:
        # Vérifier si l'appareil existe déjà pour cet utilisateur et ce token
        device, created = FCMDevice.objects.get_or_create(
            user=users,
            registration_id=fcm_token,
            defaults={"type": "android"}, 
        )
        if created:
            content =  {"success": "Device registered successfully."}
            return Response(data= content , status=status.HTTP_201_CREATED)
        
        content = {"message": "Device already registered."}
        return  Response(data= content , status=status.HTTP_200_OK) 
    
    except Exception as e:
        content = {"error": f"An error occurred: {str(e)}"}
        return  Response(data= content , status=status.HTTP_400_BAD_REQUEST) 
