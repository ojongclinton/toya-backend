from rest_framework import status 
from rest_framework.response import Response 
from rest_framework.request import Request 
from rest_framework.decorators import api_view , permission_classes 
from clients.models import Clients 
import re
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from ..customs import JWT
from rides.models import Rides 
from django.db.models import Count , Sum


@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_all_client(request: Request, *args, **kwargs):
    """
    Récupère tous les clients avec leurs détails, 
    y compris le nombre de courses et le total dépensé.
    """
    try:
        token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
        
        clients = Clients.objects.values(
            "id", "username", "email", "first_name", "last_name", 
            "phone_number", "adresse", "date_joined", "referral_code"
        )
        
        client_data = []
        for client in clients:
            client_id = client["id"]
            
            rides_info = Rides.objects.filter(client_id=client_id , status ='completed').aggregate(
                total_spent=Sum("final_price"), 
                total_rides=Count("id")
            )
            
            client["total_rides"] = rides_info["total_rides"] or 0
            client["total_spent"] = rides_info["total_spent"] or 0.0
            client_data.append(client)

        content = {"Message": "Tous les clients récupérés avec succès", "Data": client_data}
        return Response(data=content, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            data={"Message": f"Erreur lors de la récupération des clients : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_details_of_client(request:Request , client_id :str , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        
        client = Clients.objects.get(id = client_id)
        rides_info = Rides.objects.filter(client_id=client.id , status ='completed' ).aggregate(
                total_spent=Sum("final_price"), 
                total_rides=Count("id")
            )
        
        data = { 
                'id' : client.id, 
                'username' :client.id,  
                'email' : client.email, 
                'first_name' : client.first_name, 
                'last_name' : client.last_name, 
                'phone_number' : client.phone_number, 
                'adresse' : client.adresse, 
                "date_joined":client.date_joined, 
                "referral_code":client.referral_code, 
                'total_rides':rides_info["total_rides"] or 0 ,
                'total_spent' : rides_info["total_spent"] or 0.0
                
                }
    except Exception as e : 
        content  = {"Message":"User does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    content = {"Message":'Clients Details',"Data":data}
    return Response(data=content , status=status.HTTP_200_OK)
    
    
    
@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_client_account(request:Request , client_id :str , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        
        client = Clients.objects.get(id = client_id)
        client.delete()
        
    except Exception as e : 
        content  = {"Message":"User does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    content = {"Message":'Customer account deleted'}
    return Response(data=content , status=status.HTTP_200_OK)


@extend_schema(
    tags=['BackOffice Clients'], 
    request={
            'application/json': {
                'properties': {
                    'username': {'type': 'string', 'example': 'username'},
                    'first_name': {'type': 'string', 'example': 'first_name'}, 
                    'last_name': {'type': 'string', 'example': 'last_name'},
                    'phone_number': {'type': 'string', 'example': 'phone_number'},
                    'adresse': {'type': 'string', 'example': 'adresse'},
                }
            }
    }, 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_client_account(request:Request ,client_id :str,  *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        client = Clients.objects.get(id = client_id)
    except Clients.DoesNotExist : 
        content  = {"Message":"User does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    username = request.data.get('username', None)
    first_name = request.data.get('first_name',None)
    last_name = request.data.get('last_name',None)
    phone_number = request.data.get('phone_number',None)
    adresse = request.data.get('adresse',None)
    
    if username:
        client.username = username
    if first_name:
        client.first_name = first_name
    if last_name:
        client.last_name = last_name
    if phone_number:
        
        pattern = r"^\+2376\d{8}$"
    
        if not re.match(pattern, phone_number) : 
            content = {"Message": "Invalid phone number. It should start with +2376 and be followed by 9 digits."}
            return Response(data = content , status = status.HTTP_400_BAD_REQUEST)
        
        client.phone_number = phone_number
        
    if adresse:
        client.adresse = adresse
        
    client.save()
    
    content = {"Message": "User Updated Successfully",}
    return Response(data = content , status = status.HTTP_200_OK)

