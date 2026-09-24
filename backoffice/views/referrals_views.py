from rest_framework import status 
from rest_framework.response import Response 
from rest_framework.request import Request 
from rest_framework.decorators import api_view , permission_classes 
from referrals.models import ReferralsClient ,ReferralsDrivers  
from ..serializers import * 
from drf_spectacular.utils import extend_schema
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated



@extend_schema(
    tags=['BackOffice Referrals'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_all_clients_referrals(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    referrals = ReferralsClient.objects.all()
    serializer = ReferralsClientSerializer(referrals ,many=True)
    
    content = {"Message":'All Referrals Client', "Data":serializer.data}
    
    return Response(data=content , status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Referrals'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_all_drivers_referrals(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    referrals = ReferralsDrivers.objects.all()
    serializer = ReferralsDriversSerializer(referrals ,many=True)
    
    content = {"Message":'All Referrals Drivers', "Data":serializer.data}
    
    return Response(data=content , status=status.HTTP_200_OK)


@extend_schema(
    tags=['BackOffice Referrals'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_details_of_clients_referrals(request:Request , referrals_id :str , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        referrals = ReferralsClient.objects.get(id = referrals_id)
        
    except ReferralsClient.DoesNotExist as e : 
        content  = {"Message":"Referrals does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    data = {"referrals_id": referrals.id, 
                "referrals_code": referrals.referrer_client_id.referral_code, 
                "total_number_of_uses":ReferralsClient.objects.filter(referrer_client_id = str(referrals.referrer_client_id.id)).count() or 0 
                }
                
    content = {"Message":'Referrals details',"Data":data}
    
    return Response(data=content , status=status.HTTP_200_OK)
    
    
    
    
    
    
    
@extend_schema(
    tags=['BackOffice Referrals'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_details_of_drivers_referrals(request:Request , referrals_id :str , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        referrals = ReferralsDrivers.objects.get(id = referrals_id)
        
    except ReferralsDrivers.DoesNotExist as e : 
        content  = {"Message":"Referrals does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    data = {"referrals_id": referrals.id, 
                "referrals_code": referrals.referrer_driver_id.referral_code, 
                "total_number_of_uses":ReferralsDrivers.objects.filter(referrer_driver_id = str(referrals.referrer_driver_id.id)).count() or 0 
                }
                
    content = {"Message":'Referrals details',"Data":data}
    
    return Response(data=content , status=status.HTTP_200_OK)
    
    