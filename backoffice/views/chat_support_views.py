from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from clients.models import Clients 
from drivers.models import Drivers 
from support.models import SupportsConversation
from backoffice.models import BackofficeAdmin
from ..customs import JWT
from support.serializers import * 



@extend_schema(
    tags=['Supports Conversation'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_support_conversations(request: Request):
    """
    Récupère toutes les discussions de support disponibles.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    try:
        conversation_list = SupportsConversation.objects.all().select_related('sender_id', 'receiver_id')
    except SupportsConversation.DoesNotExist:
        return Response(
            {"Message": "Aucune conversation de support trouvée."},
            status=status.HTTP_404_NOT_FOUND
        )

    all_conversations = []

    for conversation in conversation_list:
        sender = retrieve_user_data(str(conversation.sender_id))
        receiver = retrieve_user_data(str(conversation.receiver_id))

        sender_picture_path = request.build_absolute_uri(sender.get("profile_picture", None))
        receiver_picture_path = request.build_absolute_uri(receiver.get("profile_picture", None))

        # Identifier l’interlocuteur du backoffice
        if sender.get("type_of_user") == "backoffice":
            interlocutor_name = "Support TOYA"
            interlocutor_type = "support"
            other_user_name = receiver.get("full_name")
            other_user_type = receiver.get("type_of_user")
        elif receiver.get("type_of_user") == "backoffice":
            interlocutor_name = "Support TOYA"
            interlocutor_type = "support"
            other_user_name = sender.get("full_name")
            other_user_type = sender.get("type_of_user")
        else:
            interlocutor_name = None
            interlocutor_type = None
            other_user_name = None
            other_user_type = None

        message_data = {
            "ticket_id": str(conversation.ticket_id),
            "support_name": "Support TOYA",
            "other_user": {
                "name": other_user_name,
                "type": other_user_type
            },
            "Sender Data": {
                "sender_id": sender.get("id"),
                "sender_full_name": "Support TOYA" if sender.get("type_of_user") == "backoffice" else sender.get("full_name"),  
                "sender_profile_picture": sender_picture_path,
                "type_of_user": sender.get('type_of_user'),
            },
            "Receiver Data": {
                "receiver_id": receiver.get("id"),
                "receiver_full_name": "Support TOYA" if receiver.get("type_of_user") == "backoffice" else receiver.get("full_name"),
                "receiver_profile_picture": receiver_picture_path,
                "type_of_user": receiver.get('type_of_user'),
            },
            "interlocutor_full_name": interlocutor_name,
            "interlocutor_type": interlocutor_type
        }
        all_conversations.append(message_data)

    content = {
        "Message": "Toutes les discussions de support.",
        "Data": all_conversations  
    }

    return Response(data=content, status=status.HTTP_200_OK)




@extend_schema(
    tags=['Supports Conversation'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    
)
@api_view(['GET'])
def retrieve_support_conversation_by_ticket(request:Request, ticket_id:str) : 
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

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
    tags=['Supports Conversation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_support_conversation(request: Request, ticket_id: str):
    """
    Supprime toutes les conversations liées à un ticket de support.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer les conversations du ticket
    conversations = SupportsConversation.objects.filter(ticket_id=ticket_id)
    
    if not conversations.exists():
        content = {"Message": "Aucune conversation trouvée pour ce ticket"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    # Compter avant suppression
    count = conversations.count()
    
    # Supprimer
    conversations.delete()
    
    content = {
        "Message": "Conversations supprimées avec succès",
        "deleted_count": count
    }
    return Response(data=content, status=status.HTTP_200_OK)

def retrieve_user_data(user_id):
    """
    Récupère les données d'un utilisateur en fonction de son type (Clients, Drivers, ou BackofficeAdmin).
    """
    try:
        user = Clients.objects.get(id=str(user_id))
        type_of_user = 'client'
    except Clients.DoesNotExist:
        try:
            user = Drivers.objects.get(id=str(user_id))
            type_of_user = 'driver'
        except Drivers.DoesNotExist:
            try:
                user = BackofficeAdmin.objects.get(id=str(user_id))
                type_of_user = 'backoffice'
            except BackofficeAdmin.DoesNotExist:
                return {"full_name": "Utilisateur inconnu", "profile_picture": None,"type_of_user":None }

    return {
        "id": f"{user.id}",
        "full_name": f"{user.first_name} {user.last_name}",
        "profile_picture": user.profile_picture.url if user.profile_picture else None, 
        "type_of_user":type_of_user

    }
