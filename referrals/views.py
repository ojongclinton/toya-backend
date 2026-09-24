from rest_framework.request import Request 
from drf_spectacular.utils import extend_schema 
from rest_framework import status 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view ,permission_classes 
from rest_framework.permissions import IsAuthenticated
from .models import ReferralsClient , ReferralsDrivers
from .serializers import ReferralsClientSerializer , ReferralsDriversSerializer
from clients.customs import JWT as JWT_CLIENT
from drivers.customs import JWT  as JWT_DRIVER
from clients.models import Clients
from drivers.models import Drivers
from django.db.models import Sum
from notifications.models import Notifications


@extend_schema(
    tags=['Referrals'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_clients_referrals(request:Request, *args, **kwargs) : 
    _ , users = JWT_CLIENT.filter_and_decode_token(request.headers.get("Authorization"))
    referrals = ReferralsClient.objects.filter(referrer_client_id = users.id)

    referrals_count = referrals.count() or 0 
    content = {'Message':"All Referrals", "Total number of referrals":referrals_count}
    return Response(data=content, status=status.HTTP_200_OK)
     
     
@extend_schema(
    tags=['Referrals'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_get_referral_earnings(request:Request , *args, **kwargs): 
    _ , users = JWT_CLIENT.filter_and_decode_token(request.headers.get("Authorization"))
    referrer_clients = ReferralsClient.objects.filter(referrer_client_id = users)
    all_gains_used   = referrer_clients.filter(used = True).aggregate(Sum('referral_bonus'))['referral_bonus__sum']

    all_gains_unused = referrer_clients.aggregate(Sum('referral_bonus'))['referral_bonus__sum']
    

    if not all_gains_unused : 
        all_gains_unused = 0  
        
    if not all_gains_used : 
        all_gains_used = 0 
        
        
    content = {"Messages":"All clients refferals earnings" , 'Data':{'all_gains_unused':all_gains_unused , "all_gains_used":all_gains_used }}
    return Response(data = content , status=status.HTTP_200_OK)
    
     

@extend_schema(
    tags=['Referrals'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_drivers_referrals(request:Request, *args, **kwargs) : 
    _ , users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    referrals = ReferralsDrivers.objects.filter(referrer_driver_id = users)
    
    referrals_count = referrals.count() or 0 
    content = {'Message':"All Referrals", "Total number of referrals":referrals_count}
    return Response(data=content, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Referrals'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def drivers_get_referral_earnings(request:Request , *args, **kwargs): 
    _ , users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    # referrals = ReferralsDrivers.objects.filter(referrer_driver_id = users)
    
    referrer_drivers = ReferralsDrivers.objects.filter(referrer_driver_id = users)
    all_gains_used   = referrer_drivers.filter(used = True).aggregate(Sum('referral_bonus'))['referral_bonus__sum']

    all_gains_unused = referrer_drivers.aggregate(Sum('referral_bonus'))['referral_bonus__sum']
    

    if not all_gains_unused : 
        all_gains_unused = 0  
        
    if not all_gains_used : 
        all_gains_used = 0 
        
        
    content = {"Messages":"All Drivers refferals earnings" , 'Data':{'all_gains_unused':all_gains_unused , "all_gains_used":all_gains_used }}
    return Response(data = content , status=status.HTTP_200_OK)


@extend_schema(
    tags=['Referrals'], 
    request= ReferralsClientSerializer, 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_clients_referrals(request:Request, *args, **kwargs) : 
    invite_referral = request.data.get('invite_referral_code')
    _ , users = JWT_CLIENT.filter_and_decode_token(request.headers.get("Authorization"))
    try : 
        client = Clients.objects.get(referral_code = invite_referral)
    except Clients.DoesNotExist : 
        content = {"Message":"Clients Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    
    all_referral = ReferralsClient.objects.filter(referrer_client_id = client)
    all_referral_count = all_referral.count()
    
    if all_referral_count <= 100 : 
        try : 
            referrals_client = ReferralsClient.objects.create( 
                                                        referrer_client_id = client ,    
                                                        referred_client_id = users  
                                                            )
            referrals_client.save()
        except Exception as e : 
            content = {"Message":f"{e}"}
            return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
            
        content = {"Message":"Referrals applied"}
        
        notifications = Notifications.objects.create( 
                                                 sender = Clients.objects.get(id=users.id), 
                                                 recipient = client, 
                                                 notification_type ='referral', 
                                                 message = f"Congratulations! You've referred a customer. Take advantage of your referral benefits.", 
                                                 event_id = referrals_client.id
                                                  )
        notifications.save()
        return Response(data=content , status=status.HTTP_200_OK)
    
    else : 
        content = {"Message":"Your can Referrer by this user this user has atteint his limite "}
        return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
        



@extend_schema(
    tags=['Referrals'], 
    request= ReferralsClientSerializer, 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_drivers_referrals(request:Request, *args, **kwargs) : 
        
    invite_referral = request.data.get('invite_referral_code')
    _ , users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    try : 
        drivers = Drivers.objects.get(referral_code = invite_referral)
    except Drivers.DoesNotExist : 
        content = {"Message":"Drivers Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    all_referral = ReferralsDrivers.objects.filter( referrer_driver_id = drivers)
    all_referral_count = all_referral.count()
    
        
    if all_referral_count <= 100 : 
        try : 
            referrals_drivers = ReferralsDrivers.objects.create( 
                                                 referrer_driver_id = drivers ,    
                                                 referred_driver_id = users  
                                                      )
            referrals_drivers.save()
        except Exception as e : 
            content = {"Message":f"{e}"}
            return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
        
        notifications = Notifications.objects.create( 
                                                 sender = Drivers.objects.get(id=users.id), 
                                                 recipient = drivers, 
                                                 notification_type ='referral', 
                                                 message = f"Congratulations! You've referred a customer. Take advantage of your referral benefits.", 
                                                 event_id = referrals_drivers.id
                                                  )
        notifications.save()
        content = {"Message":"Referrals applied"}
        return Response(data=content , status=status.HTTP_200_OK)
    
    else : 
        content = {"Message":"Your can Referrer by this user this user has atteint his limite "}
        return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
