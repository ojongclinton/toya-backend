from rest_framework import status 
from rest_framework.decorators import api_view , permission_classes 
from rest_framework.response import Response 
from rest_framework.request import Request 
from .models import Conversation
from clients.models import Clients
from drivers.models import Drivers
from django.db.models import Q
from .serializers import ConversationSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.shortcuts import render , redirect
from clients.customs import JWT as JWT_Clients
from drivers.customs import JWT as JWT_Drivers
from .customs import JWT



@extend_schema(
    tags=['Conversation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_conversations(request: Request):
    """
    Retourne la liste des conversations actives avec dernier message et heure.
    """
    token, users = JWT().filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer toutes les conversations de l'utilisateur
    conversation_list = Conversation.objects.filter(
        Q(sender_id=users.id) | Q(receiver_id=users.id)
    ).order_by('-timestamp')
    
    # Regrouper par ride_id et garder le dernier message
    unique_conversations = {}
    
    for conversation in conversation_list:
        ride_id = str(conversation.rides_id.id)
        
        # Si déjà traité, vérifier si ce message est plus récent
        if ride_id in unique_conversations:
            if conversation.timestamp <= unique_conversations[ride_id]['_timestamp']:
                continue
        
        # Déterminer qui est l'interlocuteur
        if str(conversation.sender_id.id) == str(users.id):
            other_user_id = conversation.receiver_id.id
            message_sender = "you"
        else:
            other_user_id = conversation.sender_id.id
            message_sender = "other"
        
        # Récupérer les infos de l'interlocuteur
        try:
            other_user = Clients.objects.get(id=str(other_user_id))
            user_type = "client"
        except Clients.DoesNotExist:
            other_user = Drivers.objects.get(id=str(other_user_id))
            user_type = "driver"
        
        # Photo de profil
        profile_picture = None
        if other_user.profile_picture:
            profile_picture = request.build_absolute_uri(other_user.profile_picture.url)
        
        # Compter les messages non lus
        unread_count = Conversation.objects.filter(
            rides_id=conversation.rides_id,
            receiver_id=users.id,
            is_read=False
        ).count()
        
        # Récupérer le statut de la course
        from rides.models import Rides
        try:
            ride = Rides.objects.get(id=conversation.rides_id.id)
            ride_status = ride.status
        except Rides.DoesNotExist:
            ride_status = "unknown"
        
        message_data = {
            "conversation_id": str(conversation.id),
            "ride_id": ride_id,
            "ride_status": ride_status,
            "other_user": {
                "user_id": str(other_user.id),
                "user_type": user_type,
                "full_name": f"{other_user.first_name} {other_user.last_name}",
                "profile_picture": profile_picture
            },
            "last_message": {
                "text": conversation.message,
                "timestamp": conversation.timestamp.isoformat(),
                "sender": message_sender
            },
            "unread_count": unread_count,
            "_timestamp": conversation.timestamp
        }
        
        unique_conversations[ride_id] = message_data
    
    # Convertir en liste et trier par timestamp décroissant
    conversation_data = sorted(
        unique_conversations.values(),
        key=lambda x: x['_timestamp'],
        reverse=True
    )
    
    # Retirer le champ _timestamp
    for conv in conversation_data:
        del conv['_timestamp']
    
    content = {
        "Message": "All your conversations",
        "Data": conversation_data
    }
    return Response(data=content, status=status.HTTP_200_OK)



@extend_schema(
     tags=['Conversation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_by_ride(request:Request, rides_id:str) : 
    token, users = JWT().filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        conversation = Conversation.objects.filter(rides_id=rides_id)

    except Conversation.DoesNotExist : 
        content = {"Message":"conversation Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)

    serializer = ConversationSerializer(instance = conversation, many=True) 
    
    content = {"Message":"Conversation Content", "Data":serializer.data}
    return Response(data=content , status=status.HTTP_200_OK)


@extend_schema(
    tags=['Conversation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_conversations(request: Request):
    """
    Supprime toutes les conversations de l'utilisateur.
    """
    token, users = JWT().filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer toutes les conversations de l'utilisateur
    conversations = Conversation.objects.filter(
        Q(sender_id=users.id) | Q(receiver_id=users.id)
    )
    
    # Compter avant suppression
    count = conversations.count()
    
    if count == 0:
        content = {
            "Message": "Aucune conversation à supprimer",
            "deleted_count": 0
        }
        return Response(data=content, status=status.HTTP_200_OK)
    
    # Supprimer toutes les conversations
    conversations.delete()
    
    content = {
        "Message": "Toutes vos conversations ont été supprimées",
        "deleted_count": count
    }
    return Response(data=content, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Conversation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation_by_ride(request: Request, rides_id: str):
    """
    Supprime toutes les conversations liées à une course spécifique.
    """
    token, users = JWT().filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer les conversations de cette course pour cet utilisateur
    conversations = Conversation.objects.filter(
        Q(sender_id=users.id) | Q(receiver_id=users.id),
        rides_id=rides_id
    )
    
    count = conversations.count()
    
    if count == 0:
        content = {
            "Message": "Aucune conversation trouvée pour cette course",
            "deleted_count": 0
        }
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    conversations.delete()
    
    content = {
        "Message": "Conversation supprimée avec succès",
        "deleted_count": count
    }
    return Response(data=content, status=status.HTTP_200_OK)
