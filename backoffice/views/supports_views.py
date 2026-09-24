from rest_framework import status
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from clients.models import Clients
from drivers.models import Drivers
from support.models import SupportTicket
from ..serializers import SupportTicketClientSerializer, SupportTicketDriverSerializer
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated



@extend_schema(
    tags=['BackOffice Support Ticket'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_support_tickets_client(request):
    """
    Retrieve all support tickets submitted by clients.
    
    Returns tickets with ride details when linked to a specific ride.
    Includes client full name for backoffice display.
    """ 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    tickets = SupportTicket.objects.all().filter(type_user = 'client')

    data = []
    for ticket in tickets:
        client = Clients.objects.get(id=str(ticket.users_id.id))
        serializer = SupportTicketClientSerializer(ticket)
        ticket_data = serializer.data
        ticket_data['full_name'] = f"{client.first_name} {client.last_name}"
        data.append(ticket_data)

        content = {
            "Message": "List of support tickets submitted",
            "Data": data
        }


    return Response(data=content , status=status.HTTP_200_OK)


@extend_schema(
    tags=['BackOffice Support Ticket'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_support_tickets_drivers(request):
    """
    Retrieve all support tickets submitted by drivers.
    
    Returns tickets with ride details when linked to a specific ride.
    Includes driver full name for backoffice display.
    """ 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    tickets = SupportTicket.objects.all().filter(type_user = 'drivers')
    data = []
    for ticket in tickets:
        driver = Drivers.objects.get(id=str(ticket.users_id.id))
        serializer = SupportTicketDriverSerializer(ticket)
        ticket_data = serializer.data
        ticket_data['full_name'] = f"{driver.first_name} {driver.last_name}"
        data.append(ticket_data)

        content = {
            "Message": "List of support tickets submitted",
            "Data": data
        }

    return Response(data=content , status=status.HTTP_200_OK)




@extend_schema(
    tags=['BackOffice Support Ticket'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def get_support_ticket_clients(request, ticket_id):
    """
    Retrieve detailed information for a specific client support ticket.
    
    Includes ride details when the ticket is linked to a specific ride.
    Used by backoffice to view complete ticket context.

    Args:
        ticket_id (UUID): The ID of the support ticket to retrieve.

    Returns:
        Response: Complete ticket details with optional ride information.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    serializer = SupportTicketClientSerializer(ticket)
    
    content = {"Message":'support tickets details', "Data":serializer.data}

    return Response(data=content , status=status.HTTP_200_OK)




@extend_schema(
    tags=['BackOffice Support Ticket'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_support_ticket_drivers(request, ticket_id):
    """
    Retrieve the details of a specific support ticket.

    Args:
        ticket_id (UUID): The ID of the support ticket to retrieve.

    Returns:
        Response: A JSON response with the details of the specified support ticket.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    serializer = SupportTicketDriverSerializer(ticket)
    content = {"Message":'support tickets details', "Data":serializer.data}
    return Response(data=content , status=status.HTTP_200_OK)





@extend_schema(
    tags=['BackOffice Support Ticket'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def close_support_ticket_clients(request, ticket_id):
    """
    Mark a specific support ticket as resolved and closed.

    Args:
        ticket_id (UUID): The ID of the support ticket to close.

    Returns:
        Response: A JSON response indicating the result of the operation.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    ticket.status = 'resolved'
    ticket.save()
    return Response({"message": "Support ticket has been marked as resolved."}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['BackOffice Support Ticket'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def close_support_ticket_drivers(request, ticket_id):
    """
    Mark a specific support ticket as resolved and closed.

    Args:
        ticket_id (UUID): The ID of the support ticket to close.

    Returns:
        Response: A JSON response indicating the result of the operation.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    ticket.status = 'resolved'
    ticket.save()
    return Response({"message": "Support ticket has been marked as resolved."}, status=status.HTTP_200_OK)


