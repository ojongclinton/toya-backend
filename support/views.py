from rest_framework.request import Request 
from rest_framework.response import Response 
from rest_framework import status
from rest_framework.decorators import api_view  , permission_classes

from core.utils import notifications
from .serializers import SupportTicketClientSerializer , SupportTicketdDriversSerializer , FagSerializer  , SupportTicketFieldsSerializer   , SupportConversationSerializer
from .models import Fag , SupportsConversation, SupportTicket
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from clients.customs import JWT  as JWT_Client
from drivers.customs import JWT as  JWT_Drivers
from notifications.models import Notifications
from conversation.customs import JWT as JWT_Customs
from django.db.models import Q
from notifications.custums import RetrieveBackofficeUser
from clients.models import Clients
from drivers.models import Drivers
from backoffice.models import BackofficeAdmin 
from django.core.cache import cache
from core.utils.translations import get_message
from core.utils.language import get_user_language
from core.utils.notifications import send_notification_with_push


@extend_schema(
    tags=['Supports'],
    summary="Create Driver Support Ticket",
    description="Create a new support ticket for a driver. The ticket can optionally be linked to a specific ride.",
    request=SupportTicketFieldsSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        400: {'type': 'object', 'properties': {'errors': {'type': 'object'}}}
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_support_ticket_drivers(request: Request, *args, **kwargs):
    token, driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    support = request.data.copy()
    
    support['users_id'] = driver_decode.id
    support['type_user'] = 'drivers'
    
    serializer = SupportTicketdDriversSerializer(data=support) 
    
    if serializer.is_valid(): 
        ticket = serializer.save()
        
        # Récupérer un admin par défaut
        try:
            admin = BackofficeAdmin.objects.first()
            if not admin:
                return Response(
                    {"error": "Aucun administrateur disponible pour traiter le ticket"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except BackofficeAdmin.DoesNotExist:
            return Response(
                {"error": "Aucun administrateur trouvé"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Créer conversation initiale
        SupportsConversation.objects.create(
            ticket_id=ticket,
            sender_id=Drivers.objects.get(id=driver_decode.id),
            receiver_id=admin,
            message=f"Ticket créé : {ticket.issue_description}",
            is_read=False
        )
        
        content = {"message": "Support Ticket Drivers Was created", "ticket_id": str(ticket.id)} 
        
        # Notification au backoffice
        user_id = RetrieveBackofficeUser().retrieve_backoffice_user(driver_decode.id)
        send_notification_with_push(

            sender=Drivers.objects.get(id=driver_decode.id),

            recipient=user_id,

            notification_type='support_ticket_created',

            message_key='support_ticket_created',

            event_id=""

        )
        notifications.save()
        
        return Response(data=content, status=status.HTTP_200_OK)
    else:
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
     
@extend_schema(
    tags=['Supports'],
    summary="Create Client Support Ticket",
    description="Create a new support ticket for a client. The ticket can optionally be linked to a specific ride.",
    request=SupportTicketFieldsSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        400: {'type': 'object', 'properties': {'errors': {'type': 'object'}}}
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_support_ticket_clients(request: Request, *args, **kwargs):
    token, client_decode = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    support = request.data.copy()
    
    support['users_id'] = client_decode.id
    support['type_user'] = 'clients'
    
    serializer = SupportTicketClientSerializer(data=support) 
    
    if serializer.is_valid(): 
        ticket = serializer.save()
        
        # Récupérer un admin par défaut
        try:
            admin = BackofficeAdmin.objects.first()
            if not admin:
                return Response(
                    {"error": "Aucun administrateur disponible pour traiter le ticket"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except BackofficeAdmin.DoesNotExist:
            return Response(
                {"error": "Aucun administrateur trouvé"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Créer conversation initiale
        SupportsConversation.objects.create(
            ticket_id=ticket,
            sender_id=Clients.objects.get(id=client_decode.id),
            receiver_id=admin,
            message=f"Ticket créé : {ticket.issue_description}",
            is_read=False
        )
        
        content = {"message": "Support Ticket Client Was created", "ticket_id": str(ticket.id)} 
        
        # Notification au backoffice
        user_id = RetrieveBackofficeUser().retrieve_backoffice_user(client_decode.id)
        send_notification_with_push(

            sender=Clients.objects.get(id=client_decode.id),

            recipient=user_id,

            notification_type='support_ticket_created',

            message_key='support_ticket_created',

            event_id=""

        )
        notifications.save()
                
        return Response(data=content, status=status.HTTP_200_OK)
    else:
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        

@extend_schema(
    tags=['Fags'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_get_all_fag(request:Request , *args, **kwargs):
    
    token , driver_decode = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    all_fags = Fag.objects.filter(type_user = 'client') 
    serializer = FagSerializer(all_fags, many=True)
    content = {"Message":'Fags', 'Data':serializer.data}
    
    return Response(data=content , status=status.HTTP_200_OK)
    
    
@extend_schema(
     tags=['Fags'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_get_all_fag(request:Request ,*args, **kwargs):
    token , client_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    all_fags = Fag.objects.filter(type_user = 'drivers')  
    serializer = FagSerializer(all_fags, many=True)
    content = {"Message":'Fags', 'Data':serializer.data}
    
    return Response(data=content , status=status.HTTP_200_OK)



@extend_schema(
    tags=['Supports'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_support_conversations(request: Request):
    token, users = JWT_Customs().filter_and_decode_token(request.headers.get("Authorization"))
    
    conversation_list = SupportsConversation.objects.filter(
        Q(sender_id=users.id) | Q(receiver_id=users.id)
    )
    
    unique_conversations = {}
    
    for conversation in conversation_list:
        try: 
            sender = Clients.objects.get(id=str(conversation.sender_id))
        except Clients.DoesNotExist: 
            try: 
                sender = Drivers.objects.get(id=str(conversation.sender_id))
            except Drivers.DoesNotExist: 
                sender = BackofficeAdmin.objects.get(id=str(conversation.sender_id))
        
        try: 
            receiver = Clients.objects.get(id=str(conversation.receiver_id))
        except Clients.DoesNotExist: 
            try: 
                receiver = Drivers.objects.get(id=str(conversation.receiver_id))
            except Drivers.DoesNotExist: 
                receiver = BackofficeAdmin.objects.get(id=str(conversation.receiver_id))
        
        sender_picture_path = request.build_absolute_uri(sender.profile_picture.url if sender.profile_picture else None)
        receiver_picture_path = request.build_absolute_uri(receiver.profile_picture.url if receiver.profile_picture else None)
        
        message_data = {
            "ticket_id": str(conversation.ticket_id),
            "created_at": conversation.created_at.strftime('%d %b %Y, %H:%M'), 
            "timestamp": conversation.created_at.isoformat(),  
            "is_read": conversation.is_read,  
            "Sender Data": {
                "sender_id": sender.id, 
                "sender_full_name": "Support TOYA" if isinstance(sender, BackofficeAdmin) else f"{sender.first_name} {sender.last_name}",
                "sender_profile_picture": sender_picture_path,
            },
            "Receiver Data": {
                "receiver_id": receiver.id,
                "receiver_full_name": "Support TOYA" if isinstance(receiver, BackofficeAdmin) else f"{receiver.first_name} {receiver.last_name}",
                "receiver_profile_picture": receiver_picture_path,
            }
        }
        unique_conversations[conversation.ticket_id] = message_data
    
    conversation_data = list(unique_conversations.values())
    
    content = {
        "Message": "All your Conversation",
        "Data": conversation_data  
    }
    
    return Response(data=content, status=status.HTTP_200_OK)









@extend_schema(
     tags=['Supports'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_support_conversation_by_ticket(request:Request, ticket_id:str) : 
    token, users = JWT_Customs().filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        conversation = SupportsConversation.objects.filter(ticket_id=ticket_id)

    except SupportsConversation.DoesNotExist : 
        content = {"Message":"conversation Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)

    print(conversation)
    serializer = SupportConversationSerializer(instance = conversation, many=True) 
    
    content = {"Message":"Conversation Content", "Data":serializer.data}
    return Response(data=content , status=status.HTTP_200_OK)


@extend_schema(
    tags=['Supports'],
    summary="Get Client Support Tickets",
    description="Retrieve all support tickets created by the authenticated client with ride details when linked.",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'Message': {'type': 'string'},
                'Data': {'type': 'array', 'items': {'$ref': '#/components/schemas/SupportTicketClient'}}
            },
            'example': {
                'Message': 'Client support tickets',
                'Data': [
                    {
                        'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                        'ride_id': 'ride-uuid-here',
                        'ride_details': {
                            'id': 'ride-uuid-here',
                            'driver_name': 'John Doe',
                            'start_location': 'Yaoundé Centre',
                            'end_location': 'Aéroport',
                            'status': 'completed',
                            'final_price': 2500.0
                        },
                        'issue_description': 'Driver overcharged me',
                        'status': 'open',
                        'created_at': '2025-01-17T15:45:00Z'
                    }
                ]
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_client_support_tickets(request: Request):
    """Récupère tous les tickets de support du client avec détails des courses"""
    token, client = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer les tickets du client
    tickets = SupportTicket.objects.filter(users_id=client.id).order_by('-created_at')
    
    serializer = SupportTicketClientSerializer(tickets, many=True)
    
    content = {
        "Message": "Client support tickets",
        "Data": serializer.data
    }
    
    return Response(data=content, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Supports'],
    summary="Get Driver Support Tickets",
    description="Retrieve all support tickets created by the authenticated driver with ride details when linked.",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'Message': {'type': 'string'},
                'Data': {'type': 'array', 'items': {'$ref': '#/components/schemas/SupportTicketDriver'}}
            },
            'example': {
                'Message': 'Driver support tickets',
                'Data': [
                    {
                        'id': 'c3d4e5f6-g7h8-9012-cdef-g34567890123',
                        'ride_id': 'ride-uuid-here',
                        'ride_details': {
                            'id': 'ride-uuid-here',
                            'client_name': 'Jane Smith',
                            'start_location': 'Yaoundé Centre',
                            'end_location': 'Aéroport',
                            'status': 'completed',
                            'final_price': 2500.0
                        },
                        'issue_description': 'Client refused to pay',
                        'status': 'open',
                        'created_at': '2025-01-17T16:20:00Z'
                    }
                ]
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_driver_support_tickets(request: Request):
    """Récupère tous les tickets de support du conducteur avec détails des courses"""
    token, driver = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer les tickets du conducteur
    tickets = SupportTicket.objects.filter(users_id=driver.id).order_by('-created_at')
    
    serializer = SupportTicketdDriversSerializer(tickets, many=True)
    
    content = {
        "Message": "Driver support tickets",
        "Data": serializer.data
    }
    
    return Response(data=content, status=status.HTTP_200_OK)

#Endpoints pour les langues


@extend_schema(
    tags=['Settings'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'language': {'type': 'string', 'enum': ['fr', 'en']},
                'device_id': {'type': 'string'}
            },
            'required': ['language', 'device_id']
        }
    }
)
@api_view(['POST'])
def set_language(request):
    """
    Définit la langue de l'utilisateur.
    Pas de token requis - appelé avant login.
    
    Body:
    {
        "language": "fr" | "en",
        "device_id": "unique_device_id"
    }
    """
    language = request.data.get('language', 'fr')
    device_id = request.data.get('device_id')
    
    if language not in ['fr', 'en']:
        return Response({
            "Message": "Invalid language. Use 'fr' or 'en'."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not device_id:
        return Response({
            "Message": "device_id is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Stocker dans Redis (expire après 90 jours)
    cache_key = f"language_{device_id}"
    cache.set(cache_key, language, timeout=60*60*24*90)
    
    return Response({
        "Message": "Language preference saved",
        "Language": language
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Settings']
)
@api_view(['GET'])
def get_language(request):
    """
    Récupère la langue de l'utilisateur.
    
    Query params:
    - device_id: ID du device
    """
    device_id = request.GET.get('device_id')
    
    if not device_id:
        return Response({
            "Message": "device_id required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    cache_key = f"language_{device_id}"
    language = cache.get(cache_key, 'fr')  # Défaut: français
    
    return Response({
        "Language": language
    }, status=status.HTTP_200_OK)