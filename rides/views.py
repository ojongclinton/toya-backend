from rest_framework import status 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response 
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated

from core.utils import notifications
from .serialiazers import  * 
from .models import Rides , ReviewRating
from drf_spectacular.utils import extend_schema 
from .custom import RidesEstimateamount
from drivers.models import Drivers , Vehicle
from django.utils import timezone
from django.db.models import Avg
from drivers.customs  import JWT as JWT_Drivers
from clients.customs  import JWT as  JWT_Client
from notifications.models import Notifications
from django.db.models import Sum
from promotions.models import Promotions , ApplyPromotions 
from clients.models import Clients
from navigation.customs import RideAssignmentToDriver 
from navigation.localisation import GoogleMaps
from conversation.customs import JWT as JWT_FOR_ALL
from referrals.models import ReferralsClient
from payments.utils import DriverEarningsSettlement
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from core.utils.translations import get_message
from core.utils.language import get_user_language
from core.utils.notifications import send_notification_with_push

# ------------------------------------------- RIDES FOR CLIENTS  -------------------------------------------

@extend_schema(
    tags=['Rides'], 
    request=RideClientRequestSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_request_rides(request: Request, *args, **kwargs):
    token, users = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    
    active_ride = Rides.objects.filter(
        client_id=users,
        status__in=['pending', 'accepted_by_driver', 'in_progress']
    ).first()
    
    if active_ride:
        return Response({
            "Message": "You already have an active ride",
            "active_ride_id": str(active_ride.id),
            "status": active_ride.status
        }, status=status.HTTP_400_BAD_REQUEST)
        
    client_request_ride_data = request.data
    client_request_ride_data['client_id'] = users.id


    start_destination = (request.data.get('lat_start_location', None), request.data.get('lon_start_location', None))
    end_destination = (request.data.get('lat_end_location', None), request.data.get('lon_end_location', None))
    
    data = GoogleMaps().calcul_distance_beetween_localisation(start_destination, end_destination)

    # Handle case where Google Maps API fails to find a route
    if not data or not isinstance(data, dict):
        content = {
            "Message": "Unable to calculate route for the provided locations. Please verify the coordinates are valid and accessible."
        }
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)

    distance = data["distance"]
    duration = data["duration"]
    duration_traffic = data["duration_in_traffic"]
    congestion = data["congestion_info"]


    
    try : 
        ride_estimate = RidesEstimateamount()

        duration_min = ride_estimate.parse_duration_to_minutes(duration)
        duration_traffic = ride_estimate.parse_duration_to_minutes(duration_traffic)

        fares = ride_estimate.estimate_fares(distance_km=float(distance), duration_min=duration_min , duration_in_traffic= duration_traffic , congestion_info=congestion)
        
        estimate_amount_economy = fares["economy"]
        estimate_amount_confort = fares["comfort"]
        estimate_amount_prestige = fares["prestige"]
        
    except Exception as e : 
        print(e)

    if client_request_ride_data['prestation'] == "economy":
        client_request_ride_data['final_price'] = estimate_amount_economy
    elif client_request_ride_data['prestation'] == "confort":
        client_request_ride_data['final_price'] = estimate_amount_confort
    elif client_request_ride_data['prestation'] == "prestige":
        client_request_ride_data['final_price'] = estimate_amount_prestige
    
    
    final_price = client_request_ride_data['final_price']

    # referral_discount = 0
    # referral = ReferralsClient.objects.filter(referrer_client_id=users.id, used=False).first()
    # if referral:
    #     referral_discount = referral.referral_bonus
    #     final_price *= (1 - referral_discount / 100) 
    #     print(f"referral_discount price :{final_price}") 

    
    code_promo = request.data.get('code_promo', None)
    if code_promo:
        try:
            code = Promotions.objects.get(code=code_promo)
            apply_promo = ApplyPromotions.objects.filter(promotions_id=code.id, client_id=users.id)
            # if apply_promo.exists():
            #     content = {"Message": "The customer has already used this promotional code."}
            #     return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
            
            total_usage_code_promo = ApplyPromotions.objects.filter(promotions_id=code.id).count() or 0
            print("pass")
            if total_usage_code_promo <= code.usage_limit:
                if code.status == 'not_started':
                    content = {"Message": "This promotion has not yet started. Please try again after the start date."}
                    return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
                elif code.status == 'expired':
                    content = {"Message": "This promotion has expired. Please use another promo code or continue without a promotion."}
                    return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    final_price *= (1 - code.discount_percentage / 100)
                    print(f"promotions price :{final_price}") 
                    client = Clients.objects.get(id=users.id)
                    promotions = ApplyPromotions.objects.create(client_id=client, promotions_id=code)
                    promotions.save()
            else:
                content = {"Message": "You cannot use this code because the limit has been reached."}
                return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
        except Promotions.DoesNotExist:
            # content = {"Message": "Promo Code Does not Exist"}
            # return Response(data=content, status=status.HTTP_404_NOT_FOUND)
            pass

    client_request_ride_data['final_price'] = final_price
    client_request_ride_data['distance'] = distance  # Add the calculated distance
    print(f"final price :{final_price}") 
    client_request_ride_data.pop('code_promo', None)

    serializer = RideClientRequestsSerializer(data=client_request_ride_data)
    if serializer.is_valid():
        data = serializer.save()

        # Broadcast au backoffice
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'backoffice_notifications',
            {
                'type': 'ride_created',
                'ride_id': str(data.id),
                'client_name': f"{users.first_name} {users.last_name}",
                'pickup_location': request.data.get('start_location'),
                'destination': request.data.get('end_location'),
                'prestation': request.data.get('prestation'),
                'price': float(final_price),
                'timestamp': timezone.now().isoformat()
            }
        )
        
        from navigation.customs import notify_nearby_drivers
        notify_nearby_drivers(
            ride_id=data.id,
            pickup_lat=data.lat_start_location,
            pickup_lon=data.lon_start_location,
            prestation=data.prestation,
            radius_km=10
        )


        # make this with celery
        rideAssignmentToDriver = RideAssignmentToDriver(data)
        
        closest_drivers = rideAssignmentToDriver.launch_rides_assignment_to_driver()
        formatted_drivers = [{"driver_id": driver.id, "distance": distance} for driver, distance in closest_drivers]
        # formatted_drivers = []
        content = {"Message": "Ride was requested", "Rides_id": serializer.data['id'], "closest_drivers": formatted_drivers}
        return Response(data=content, status=status.HTTP_200_OK)

    content = {"Message": serializer.errors}
    return Response(data=content, status=status.HTTP_400_BAD_REQUEST)



    
@extend_schema(
    tags=['Rides'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_cancel_rides(request: Request, rides_id: str, *args, **kwargs):
    """
    Client annule sa course (seulement si pending ou accepted_by_driver).
    Si un chauffeur était assigné, il est notifié et remboursé.
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from django.utils import timezone
    
    token, users = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        ride = Rides.objects.get(id=rides_id)
    except Rides.DoesNotExist:
        content = {"Message": "Ride does not exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier que la course appartient au client
    if str(ride.client_id.id) != str(users.id):
        content = {"Message": "Cette course ne vous appartient pas."}
        return Response(data=content, status=status.HTTP_403_FORBIDDEN)
    
    # Vérifier que la course est annulable
    if ride.status not in ['pending', 'accepted_by_driver']:
        if ride.status == 'in_progress':
            message = "Impossible d'annuler une course en cours."
        elif ride.status == 'completed':
            message = "Cette course est déjà terminée."
        elif ride.status == 'cancelled':
            message = "Cette course est déjà annulée."
        else:
            message = "Cette course ne peut pas être annulée."
        
        content = {"Message": message, "current_status": ride.status}
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
    
    # Si un chauffeur était assigné, le libérer et le rembourser
    commission_refunded = 0.0
    if ride.driver_id:
        driver = ride.driver_id
        
        # Rembourser la commission si le chauffeur avait accepté
        if ride.status == 'accepted_by_driver':
            from drivers.models import DriverGrade
            from payments.models import WalletTransaction
            from decimal import Decimal
            
            # Calculer la commission à rembourser
            driver_grade = DriverGrade.objects.filter(
                driver=driver, 
                is_current=True
            ).select_related('grade').first()
            
            commission_rate = driver_grade.grade.commission_rate if driver_grade else Decimal('15.00')
            ride_price = Decimal(str(ride.final_price))
            commission_amount = (ride_price * commission_rate) / 100
            
            # Rembourser
            balance_before = driver.wallet_money
            driver.wallet_money += commission_amount
            driver.save()
            
            # Créer transaction
            WalletTransaction.objects.create(
                driver=driver,
                transaction_type='commission_refund',
                amount=commission_amount,
                balance_before=balance_before,
                balance_after=driver.wallet_money,
                description=f"Remboursement - Course {ride.id} annulée par le client",
                status='completed'
            )
            
            commission_refunded = float(commission_amount)
        
        # Libérer le chauffeur
        driver.is_available = True
        driver.save()
        
        # Notification au chauffeur
        try:
            client = Clients.objects.get(id=users.id)
            
            user_language = get_user_language(user=driver)
            base_message = get_message('ride_canceled_by_client', user_language)
            
            if commission_refunded > 0:
                refund_message = get_message('commission_refunded', user_language, amount=commission_refunded)
                full_message = f"{base_message} {refund_message}"
            else:
                full_message = base_message
            
            # Créer notification en base
            send_notification_with_push(
                sender=client,
                recipient=driver,
                notification_type='ride_canceled',
                message_key='ride_canceled_by_client',
                event_id=str(ride.id)
            )
            
            # Broadcast au chauffeur via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'ride_updates_{driver.id}',
                {
                    'type': 'ride_cancelled',
                    'ride_id': str(ride.id),
                    'cancelled_by': 'client',
                    'commission_refunded': commission_refunded,
                    'title': get_message('ride_canceled_title', user_language),
                    'message': full_message
                }
            )
        except Clients.DoesNotExist:
            pass  # Continue même si le client n'existe pas
    
    # Annuler la course
    ride.status = 'cancelled'
    ride.save()
    
    # Broadcast au backoffice
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'backoffice_notifications',
        {
            'type': 'ride_cancelled',
            'ride_id': str(ride.id),
            'cancelled_by': 'client',
            'driver_refunded': commission_refunded,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    content = {
        "Message": "Course annulée avec succès.",
        "driver_refunded": commission_refunded if commission_refunded > 0 else None
    }
    return Response(data=content, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Rides'],
    request=RidesEstimateamountSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_estimate_rides(request: Request, *args, **kwargs): 
    token, users = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    
    code_promo = request.data.get('code_promo', None)
    
    start_destination = (request.data.get('lat_start_location', None), request.data.get('lon_start_location', None))
    end_destination = (request.data.get('lat_end_location', None), request.data.get('lon_end_location', None))
    
    data = GoogleMaps().calcul_distance_beetween_localisation(start_destination, end_destination)

    # Handle case where Google Maps API fails to find a route
    if not data or not isinstance(data, dict):
        content = {
            "Message": "Unable to calculate route for the provided locations. Please verify the coordinates are valid and accessible."
        }
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)

    distance = data["distance"]
    duration = data["duration"]
    duration_traffic = data["duration_in_traffic"]
    congestion = data["congestion_info"]


    ride_estimate = RidesEstimateamount()
    duration_min = ride_estimate.parse_duration_to_minutes(duration)
    duration_traffic = ride_estimate.parse_duration_to_minutes(duration_traffic)
    fares = ride_estimate.estimate_fares(distance_km=float(distance), duration_min=duration_min , duration_in_traffic= duration_traffic , congestion_info=congestion)
    
    estimate_amount_economy = fares["economy"]
    estimate_amount_confort = fares["comfort"]
    estimate_amount_prestige = fares["prestige"]
    



    data = {
        "economy": {"Normal Price": estimate_amount_economy, "Duration": duration, "Distance(Km)": distance},
        "confort": {"Normal Price": estimate_amount_confort, "Duration": duration, "Distance(Km)": distance},
        "prestige": {"Normal Price": estimate_amount_prestige, "Duration": duration, "Distance(Km)": distance},
    }

    # data_with_referral = None
    data_with_promo = None

    # try: 
    #     referral = ReferralsClient.objects.filter(referrer_client_id=users.id, used=False).first()

    #     if referral:
    #         referral_discount = referral.referral_bonus 
    #         data_with_referral = {
    #             "economy": {
    #                 "Price After Referral Discount": estimate_amount_economy * (1 - referral_discount / 100),
    #                 "Normal Price": estimate_amount_economy,
    #                 "Duration": duration,
    #                 "Distance(Km)": distance,
    #             },
    #             "confort": {
    #                 "Price After Referral Discount": estimate_amount_confort * (1 - referral_discount / 100),
    #                 "Normal Price": estimate_amount_confort,
    #                 "Duration": duration,
    #                 "Distance(Km)": distance,
    #             },
    #             "prestige": {
    #                 "Price After Referral Discount": estimate_amount_prestige * (1 - referral_discount / 100),
    #                 "Normal Price": estimate_amount_prestige,
    #                 "Duration": duration,
    #                 "Distance(Km)": distance,
    #             },
    #         }
    # except ReferralsClient.DoesNotExist:
    #     pass

    if code_promo:
        try:
            code = Promotions.objects.get(code=code_promo)
            
            apply_promo = ApplyPromotions.objects.filter(promotions_id=code.id).filter(client_id=users.id)

            total_usage_code_promo = ApplyPromotions.objects.filter(promotions_id=code.id).count() or 0
            if total_usage_code_promo <= code.usage_limit:
                if code.status == 'not_started': 
                    content = {"Message": "This promotion has not yet started. Please try again after the start date."}
                    return Response(data=content, status=status.HTTP_400_BAD_REQUEST)

                elif code.status == 'expired': 
                    content = {"Message": "This promotion has expired. Please use another promo code or continue without a promotion."}
                    return Response(data=content, status=status.HTTP_400_BAD_REQUEST)

                else:
                    data_with_promo = {
                        "economy": {
                            "Price After Promo Discount": estimate_amount_economy * (1 - code.discount_percentage / 100),
                            "Normal Price": estimate_amount_economy,
                            "Duration": duration,
                            "Distance(Km)": distance,
                        },
                        "confort": {
                            "Price After Promo Discount": estimate_amount_confort * (1 - code.discount_percentage / 100),
                            "Normal Price": estimate_amount_confort,
                            "Duration": duration,
                            "Distance(Km)": distance,
                        },
                        "prestige": {
                            "Price After Promo Discount": estimate_amount_prestige * (1 - code.discount_percentage / 100),
                            "Normal Price": estimate_amount_prestige,
                            "Duration": duration,
                            "Distance(Km)": distance,
                        },
                    }
            else: 
                content = {"Message": "You cannot use this code because the limit has been reached."}
                return Response(data=content, status=status.HTTP_400_BAD_REQUEST)

        except Promotions.DoesNotExist: 
            content = {"Message": "Promo Code Does not Exist"}
            return Response(data=content, status=status.HTTP_404_NOT_FOUND)

    final_response = {}

    if data_with_promo:
        for category in ["economy", "confort", "prestige"]:
            if category in data_with_promo:
                if category not in final_response:
                    final_response[category] = data_with_promo[category]
                else:
                    final_response[category].update(data_with_promo[category])

    # if data_with_referral:
    #     for category in ["economy", "confort", "prestige"]:
    #         if category in data_with_referral:
    #             if category not in final_response:
    #                 final_response[category] = data_with_referral[category]
    #             else:
    #                 final_response[category].update(data_with_referral[category])

    for category in ["economy", "confort", "prestige"]:
        if category not in final_response:
            final_response[category] = data[category]

    # if data_with_promo and data_with_referral:
    #     for category in ["economy", "confort", "prestige"]:
    #         if category in data_with_promo and category in data_with_referral:
    #             final_price = data_with_promo[category]["Price After Promo Discount"] * (1 - referral_discount / 100)
    #             final_response[category]["Final Price"] = final_price

    content = {"Message":"Estimated prices for your journey", 'Data':final_response}
    return Response(data=content, status=status.HTTP_200_OK)






@extend_schema(
     tags=['Rides'], 
    request=RideClientRequestSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_rides(request:Request ,rides_id:str, *args, **kwargs) : 
    token , user = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        rides = Rides.objects.filter(id = rides_id).first()
        print(rides)
    except Rides.DoesNotExist : 
        content = {"Message":"Rides Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    vehicule = Vehicle.objects.get(driver_id = rides.driver_id)
    
    if vehicule : 
        vehicle_brand = vehicule.vehicle_brand or None
        vehicle_model = vehicule.vehicle_model or None
    
    if rides.status == "in_progress" : 
        ride_data = {
            "id": str(rides.id),
            "start_location": rides.start_location,
            "end_location": rides.end_location,
            "prestation": rides.prestation,
            "mode_of_payments": rides.mode_of_payments,
            "distance": float(rides.distance),
            "final_price": float(rides.final_price),
            "is_price_promotion": rides.is_price_promotion if hasattr(rides, 'is_price_promotion') else False,
            "code_promo": rides.code_promo if hasattr(rides, 'code_promo') else None,
            "lon_start_location": rides.lon_start_location,
            "lon_end_location": rides.lon_end_location,
            "lat_start_location": rides.lat_start_location,
            "lat_end_location": rides.lat_end_location,
            "Type_Of_Véhicule" : None, 
            "accepted_time": rides.accepted_time,
            "start_time": rides.start_time,
            "end_time": rides.end_time,
            "vehicle_brand": vehicle_brand,
            "vehicle_model" : vehicle_model , 
        }
        content = {"Message":"Rides Informations","Data":ride_data}
        return Response(data=content , status=status.HTTP_200_OK)
    content = {"Message":"This Rides is no longer in progress "}
    return Response(data=content , status=status.HTTP_400_BAD_REQUEST) 


@extend_schema(
    tags=['Rides'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_track_rides(request: Request, rides_id: str, *args, **kwargs):
    """
    Track ride in real-time for clients.
    
    Returns the driver's current location, route, and driver info including grade and rating.
    
    Args:
        request (Request): The incoming HTTP request.
        rides_id (str): The ID of the ride to track.
        include_pickup_route (bool, optional): Whether to include the route driver will take to reach pickup point. Defaults to False.
        
    Returns:
        Response: Driver location, route data with polyline, driver info, or error if ride not found.
    """
    from drivers.models import Vehicle, DriverGrade
    from rides.models import ReviewRating
    from django.db.models import Avg
    
    token, users = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        rides = Rides.objects.get(id=rides_id)
    except Rides.DoesNotExist:
        content = {"Message": "Ride does not exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    # Verify the client owns this ride
    if str(rides.client_id.id) != str(users.id):
        content = {"Message": "You are not authorized to track this ride"}
        return Response(data=content, status=status.HTTP_403_FORBIDDEN)
    
    # Check ride status
    if rides.status not in ['accepted_by_driver', 'in_progress']:
        content = {
            "Message": "Ride tracking not available", 
            "reason": f"Ride status is '{rides.status}'. Tracking is only available for accepted or in-progress rides."
        }
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if driver is assigned
    if not rides.driver_id:
        content = {"Message": "No driver assigned to this ride yet"}
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
    
    driver = rides.driver_id
    
    # Get driver's current location
    from navigation.models import Position
    driver_position = Position.objects.filter(user_id=driver.id).order_by('-timestamp').first()
    
    if not driver_position:
        content = {"Message": "Driver location not available"}
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
    
    driver_location = {
        "lat": driver_position.lat,
        "lon": driver_position.lon,
        "address": driver_position.address,
        "timestamp": driver_position.timestamp.isoformat()
    }
    
    # Récupérer infos chauffeur complètes
    driver_profile_picture = None
    if driver.profile_picture:
        driver_profile_picture = request.build_absolute_uri(driver.profile_picture.url)
    
    # Grade
    driver_grade = DriverGrade.objects.filter(
        driver=driver,
        is_current=True
    ).select_related('grade').first()
    grade_name = driver_grade.grade.name if driver_grade else 'Standard'
    
    # Note moyenne + avis
    avg_rating = ReviewRating.objects.filter(driver_id=driver).aggregate(
        avg=Avg('rating')
    )['avg']
    review_count = ReviewRating.objects.filter(driver_id=driver).count()
    
    # Véhicule
    vehicle_data = None
    try:
        vehicle = Vehicle.objects.get(driver_id=driver.id)
        vehicle_photo = None
        if vehicle.photos:
            vehicle_photo = request.build_absolute_uri(vehicle.photos.url)
        
        vehicle_data = {
            "brand": vehicle.vehicle_brand,
            "model": vehicle.vehicle_model,
            "color": vehicle.vehicle_color,
            "license_plate": vehicle.license_plate,
            "photo": vehicle_photo
        }
    except Vehicle.DoesNotExist:
        pass
    
    driver_info = {
        "id": str(driver.id),
        "name": f"{driver.first_name} {driver.last_name}",
        "phone": driver.phone_number,
        "photo": driver_profile_picture,
        "grade": grade_name,
        "rating": round(float(avg_rating), 1) if avg_rating else 0.0,
        "review_count": review_count,
        "vehicle": vehicle_data
    }
    
    # Get route data based on ride status
    lang = request.GET.get("lang", 'fr')
    include_pickup_route = request.GET.get("include_pickup_route", 'false').lower() == 'true'
    rideAssignmentToDriver = RideAssignmentToDriver(rides_id=str(rides_id))
    
    route_data = None
    main_route_data = None
    
    if rides.status == 'accepted_by_driver':
        # Driver is on the way to pickup the client
        if include_pickup_route:
            all_informations, duration, distance = rideAssignmentToDriver.pickup(driver.id, lang=lang)
            
            if all_informations is not None and duration is not None and distance is not None:
                route_data = {
                    "route_type": "pickup",
                    "total_distance_km": distance,
                    "total_duration": duration,
                    "itinerary": all_informations
                }
            else:
                route_data = {
                    "route_type": "pickup",
                    "total_distance_km": "unavailable",
                    "total_duration": "unavailable",
                    "itinerary": None,
                    "error": "Unable to calculate pickup route - Google Maps API unavailable"
                }
        
        # Always include the main route (pickup to destination) for reference
        dropoff_info, dropoff_duration, dropoff_distance = rideAssignmentToDriver.dropoff(driver.id, lang=lang)
        
        if dropoff_info is not None and dropoff_duration is not None and dropoff_distance is not None:
            main_route_data = {
                "route_type": "dropoff",
                "total_distance_km": dropoff_distance,
                "total_duration": dropoff_duration,
                "itinerary": dropoff_info
            }
        else:
            main_route_data = {
                "route_type": "dropoff",
                "total_distance_km": "unavailable",
                "total_duration": "unavailable",
                "itinerary": None,
                "error": "Unable to calculate route - Google Maps API unavailable"
            }
    
    else:  # in_progress
        # Driver is taking client to destination
        all_informations, duration, distance = rideAssignmentToDriver.dropoff(driver.id, lang=lang)
        
        if all_informations is not None and duration is not None and distance is not None:
            main_route_data = {
                "route_type": "dropoff",
                "total_distance_km": distance,
                "total_duration": duration,
                "itinerary": all_informations
            }
        else:
            main_route_data = {
                "route_type": "dropoff",
                "total_distance_km": "unavailable",
                "total_duration": "unavailable",
                "itinerary": None,
                "error": "Unable to calculate route - Google Maps API unavailable"
            }
    
    content = {
        "Message": "Ride tracking information",
        "ride_status": rides.status,
        "ride_details": {
            "prestation": rides.prestation,
            "price": float(rides.final_price),
            "distance": float(rides.distance) if rides.distance else None
        },
        "driver": driver_info,
        "driver_location": driver_location,
        "main_route": main_route_data
    }
    
    # Add pickup route only if requested and available
    if route_data:
        content["pickup_route"] = route_data
    
    return Response(data=content, status=status.HTTP_200_OK)


# ------------------------------------------- RIDES FOR DRIVER  -------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def driver_accept_rides(request: Request, rides_id: str, *args, **kwargs):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from django.utils import timezone
    from rides.models import ReviewRating
    from django.db.models import Avg
    
    token, driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        rides = Rides.objects.get(id=rides_id)
    except Rides.DoesNotExist:
        content = {"Message": "Ride does not exist."}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    try:
        driver = Drivers.objects.get(id=driver_decode.id)
    except Drivers.DoesNotExist:
        content = {"Message": "Driver does not exist."}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier si le chauffeur a déjà une course active
    active_ride = Rides.objects.filter(
        driver_id=driver.id,
        status__in=['accepted_by_driver', 'in_progress']
    ).first()
    
    if active_ride:
        if active_ride.status == 'accepted_by_driver':
            message = "Vous avez déjà une course acceptée. Veuillez l'annuler avant d'en accepter une nouvelle."
            action = "cancel"
        else:  # in_progress
            message = "Vous avez une course en cours. Veuillez la terminer avant d'en accepter une nouvelle."
            action = "complete"
        
        content = {
            "Message": message,
            "active_ride_id": str(active_ride.id),
            "active_ride_status": active_ride.status,
            "action_required": action,
            "pickup_location": active_ride.start_location,
            "destination": active_ride.end_location
        }
        return Response(data=content, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vehicle = Vehicle.objects.get(driver_id=driver.id)
        if vehicle.validation_status != "validated":
            user_language = get_user_language(user=driver)
            content = {"Message": get_message('vehicle_not_validated', user_language)}
            return Response(data=content, status=status.HTTP_403_FORBIDDEN)
    except Vehicle.DoesNotExist:
        content = {"Message": "Vehicle record not found for this driver."}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    from drivers.models import DriverGrade
    from decimal import Decimal
    
    driver_grade = DriverGrade.objects.filter(
        driver=driver, 
        is_current=True
    ).select_related('grade').first()
    
    commission_rate = driver_grade.grade.commission_rate if driver_grade else Decimal('15.00')
    grade_name = driver_grade.grade.name if driver_grade else 'Standard'
    
    ride_price = Decimal(str(rides.final_price))
    commission_amount = (ride_price * commission_rate) / 100
    
    if driver.wallet_money < commission_amount:
        user_language = get_user_language(user=driver)
        content = {
            "Message": get_message('insufficient_wallet', user_language, amount=commission_amount, rate=commission_rate, grade=grade_name),
            "required_amount": float(commission_amount),
            "current_balance": float(driver.wallet_money),
            "commission_rate": float(commission_rate),
            "grade": grade_name
        }
        return Response(data=content, status=status.HTTP_403_FORBIDDEN)
    
    if rides.status == 'pending':
        driver.is_available = False
        driver.save()
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'backoffice_notifications',
            {
                'type': 'ride_accepted',
                'ride_id': str(rides.id),
                'driver_name': f"{driver.first_name} {driver.last_name}",
                'driver_id': str(driver.id),
                'timestamp': timezone.now().isoformat()
            }
        )
        
        rides.driver_id = driver
        rides.status = "accepted_by_driver"
        rides.accepted_time = timezone.now()
        rides.save()
        
        send_notification_with_push(
            sender=driver,
            recipient=rides.client_id,
            notification_type='ride_accepted',
            message_key='ride_accepted',
            event_id=rides.id
        )
        
        # Récupérer note moyenne + nombre d'avis
        avg_rating = ReviewRating.objects.filter(driver_id=driver).aggregate(
            avg=Avg('rating')
        )['avg']
        review_count = ReviewRating.objects.filter(driver_id=driver).count()
        
        # Photo véhicule
        vehicle_photo = None
        if vehicle.photos:
            vehicle_photo = request.build_absolute_uri(vehicle.photos.url)
        
        # Photo chauffeur
        driver_photo = None
        if driver.profile_picture:
            driver_photo = request.build_absolute_uri(driver.profile_picture.url)
        
        # WebSocket au client avec TOUTES les infos
        async_to_sync(channel_layer.group_send)(
            f'ride_updates_{rides.client_id.id}',
            {
                'type': 'ride_accepted',
                'ride_id': str(rides.id),
                'driver': {
                    'id': str(driver.id),
                    'name': f"{driver.first_name} {driver.last_name}",
                    'phone': driver.phone_number,
                    'photo': driver_photo,
                    'grade': grade_name,
                    'rating': round(float(avg_rating), 1) if avg_rating else 0.0,
                    'review_count': review_count
                },
                'vehicle': {
                    'brand': vehicle.vehicle_brand,
                    'model': vehicle.vehicle_model,
                    'color': vehicle.vehicle_color,
                    'license_plate': vehicle.license_plate,
                    'photo': vehicle_photo
                },
                'ride_details': {
                    'prestation': rides.prestation,
                    'price': float(rides.final_price),
                    'distance': float(rides.distance) if rides.distance else None
                },
                'accepted_time': rides.accepted_time.isoformat(),
                'message': get_message('ride_accepted', get_user_language)
            }
        )
        
        content = {"Message": "Ride was accepted by driver."}
        return Response(data=content, status=status.HTTP_200_OK)
    
    content = {"Message": "The ride is no longer available."}
    return Response(data=content, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def driver_cancel_rides(request: Request, rides_id: str, *args, **kwargs):
    token, driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        rides = Rides.objects.get(id=rides_id)
    except Rides.DoesNotExist:
        content = {"Message": "Rides Does Not Exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    try:
        driver = Drivers.objects.get(id=driver_decode.id)
    except Drivers.DoesNotExist:
        content = {"Message": "Drivers Does Not Exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    # Vérifier que la course est annulable
    if rides.status != 'accepted_by_driver':
        if rides.status == 'in_progress':
            message = "Impossible d'annuler une course en cours. Veuillez la terminer."
        elif rides.status == 'completed':
            message = "Cette course est déjà terminée."
        elif rides.status == 'cancelled':
            message = "Cette course est déjà annulée."
        else:
            message = "Cette course ne peut pas être annulée."
        
        content = {"Message": message, "current_status": rides.status}
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
    
    # Annuler la course
    driver.is_available = True
    driver.save()
    
    rides.driver_id = None
    rides.status = "pending"
    rides.save()
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'backoffice_notifications',
        {
            'type': 'ride_cancelled',
            'ride_id': str(rides.id),
            'cancelled_by': 'driver',
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'timestamp': timezone.now().isoformat()
        }
    )
    
    send_notification_with_push(
        sender=driver,
        recipient=rides.client_id,
        notification_type='ride_canceled',
        message_key='ride_canceled_by_driver',
        event_id=rides.id
    )
        
    async_to_sync(channel_layer.group_send)(
        f'ride_updates_{rides.client_id.id}',
        {
            'type': 'ride_cancelled',
            'ride_id': str(rides.id),
            'cancelled_by': 'driver',
            'message': get_message('ride_canceled_by_driver', get_user_language)
        }
    )
    
    content = {"Message": "Course annulée. Vous êtes de nouveau disponible."}
    return Response(data=content, status=status.HTTP_200_OK)
     






@extend_schema(
      tags=['Rides'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
def driver_complete_rides(request:Request , rides_id:str , *args, **kwargs) : 
    from django.db import transaction as db_transaction
    from payments.services.wallet_service import WalletService
    import logging
    
    logger = logging.getLogger(__name__)
    
    _ , driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    try : 
        rides = Rides.objects.get(id = rides_id)
    except Rides.DoesNotExist : 
        content = {"Message":"Rides Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    try : 
        driver = Drivers.objects.get(id = driver_decode.id )
    except Drivers.DoesNotExist : 
        content = {"Message":"Drivers Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    # Check if ride is in progress // this should be watched closely because it might cause issues if a new ride state is added
    if rides.status != 'in_progress':
        content = {"Message":"The Rides is no longer available "}
        return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
    
    # Use transaction to ensure atomicity
    try:
            with db_transaction.atomic():
                # 1. Update ride status
                rides.status = "completed"
                rides.end_time = timezone.now()
                rides.save()
                
                # 2. Process commission using WalletService
                result = WalletService.process_ride_commission(rides, driver)
                
                # 3. Mark driver available
                driver.is_available = True
                driver.save()
                
                # 4. Payer les bonus de parrainage si première course
                from referrals.customs import pay_referral_bonuses_after_first_ride
                pay_referral_bonuses_after_first_ride(
                    client_id=str(rides.client_id.id),
                    ride_id=str(rides.id)
                )
                
                # 5. Send notification to client
                send_notification_with_push(
                    sender=driver,
                    recipient=rides.client_id,
                    notification_type='ride_completed',
                    message_key='ride_completed',
                    event_id=rides.id
                )
                
                # 6. Broadcast ride completion to client via WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'ride_updates_{rides.client_id.id}',
                    {
                        'type': 'ride_completed',
                        'ride_id': str(rides.id),
                        'end_time': rides.end_time.isoformat(),
                        'final_price': float(rides.final_price),
                        'message': get_message('ride_completed', get_user_language)
                    }
                )
                
                # 7. Broadcast to backoffice
                async_to_sync(channel_layer.group_send)(
                    'backoffice_notifications',
                    {
                        'type': 'ride_completed',
                        'ride_id': str(rides.id),
                        'driver_name': f"{driver.first_name} {driver.last_name}",
                        'final_price': float(rides.final_price),
                        'commission': float(result['commission_amount']),
                        'timestamp': timezone.now().isoformat()
                    }
                )
            
    except ValueError as e:
        # Wallet insufficient - keep ride in progress
        # This is normally an edge case that might happen due to a system error, because the driver's wallet balance is checked before the ride is even accepted
        logger.error(f"Ride completion failed for {rides.id}: {str(e)}")
        return Response({
            "Message": "Impossible de terminer la course",
            "error": "insufficient_wallet",
            "details": str(e),
            "action_required": "Veuillez recharger votre wallet avant de terminer la course."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Unexpected error completing ride {rides.id}: {str(e)}")
        return Response({
            "Message": "Erreur lors de la terminaison de la course",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
      
      

@extend_schema(
    tags=['Rides'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
def driver_start_rides(request: Request, rides_id: str, *args, **kwargs):
    token, driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        rides = Rides.objects.get(id=rides_id)
    except Rides.DoesNotExist:
        content = {"Message": "Rides Does Not Exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    try:
        driver = Drivers.objects.get(id=driver_decode.id)
    except Drivers.DoesNotExist:
        content = {"Message": "Drivers Does Not Exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    if rides.status == 'accepted_by_driver':
        rides.driver_id = driver
        rides.status = "in_progress"
        rides.start_time = timezone.now()
        rides.save()
        
       
        channel_layer = get_channel_layer()
        
        # Broadcast au backoffice
        async_to_sync(channel_layer.group_send)(
            'backoffice_notifications',
            {
                'type': 'ride_started',
                'ride_id': str(rides.id),
                'driver_name': f"{driver.first_name} {driver.last_name}",
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Notification au client
        send_notification_with_push(

            sender=driver,

            recipient=rides.client_id,

            notification_type='start_ride',

            message_key='ride_started',

            event_id=rides.id

        )

        
        # Broadcast ride start to client via WebSocket
        async_to_sync(channel_layer.group_send)(
            f'ride_updates_{rides.client_id.id}',
            {
                'type': 'ride_started',
                'ride_id': str(rides.id),
                'start_time': rides.start_time.isoformat(),
                'message': get_message('ride_started', get_user_language)
            }
        )
        
        content = {"Message": "Rides Was Started"}
        return Response(data=content, status=status.HTTP_200_OK)
    
    content = {"Message": "The Rides is no longer available"}
    return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
 

    
@extend_schema(
    tags=['Rides'],
    summary='Get pending ride requests for driver',
    description="""
    Returns a filtered list of pending ride requests for the authenticated driver.
    
    **Filters Applied:**
    - **Geographic proximity**: Only rides within specified radius from driver's current location
    - **Prestation matching**: Only rides matching driver's vehicle type (economy/confort/prestige)
    - **Freshness**: Only recent requests within the time window
    - **Vehicle validation**: Driver must have a validated vehicle
    
    **Query Parameters:**
    - `max_distance` (optional, float): Maximum radius in km from driver to pickup point. Default: 7.0 km
    - `max_age_minutes` (optional, int): Only show requests created within last X minutes. Default: 30 minutes
    - `limit` (optional, int): Maximum number of results to return. Default: 50
    
    **Example Requests:**
    - Default filters: `GET /rides/driver/pending`
    - Wider radius: `GET /rides/driver/pending?max_distance=15`
    - Recent only: `GET /rides/driver/pending?max_age_minutes=10`
    - Combined: `GET /rides/driver/pending?max_distance=10&max_age_minutes=15&limit=25`
    
    **Response includes:**
    - List of rides sorted by distance (closest first)
    - `distance_to_pickup_km`: Distance from driver to pickup location
    - `filters_applied`: Shows active filters and cutoff time for transparency
    """,
    parameters=[
        {
            'name': 'max_distance',
            'in': 'query',
            'description': 'Maximum radius in kilometers from driver to pickup point',
            'required': False,
            'schema': {'type': 'number', 'format': 'float', 'default': 7.0, 'example': 10.0}
        },
        {
            'name': 'max_age_minutes',
            'in': 'query',
            'description': 'Only show ride requests created within the last X minutes',
            'required': False,
            'schema': {'type': 'integer', 'default': 30, 'example': 15}
        },
        {
            'name': 'limit',
            'in': 'query',
            'description': 'Maximum number of ride requests to return',
            'required': False,
            'schema': {'type': 'integer', 'default': 50, 'example': 25}
        }
    ],
    responses={
        200: {
            'description': 'List of pending ride requests',
            'content': {
                'application/json': {
                    'example': {
                        'Message': 'Rides in Pending',
                        'Data': [
                            {
                                'id': 'uuid-here',
                                'full_name': 'John Doe',
                                'client_details': {
                                    'id': 'client-uuid',
                                    'first_name': 'John',
                                    'last_name': 'Doe',
                                    'email': 'john@example.com',
                                    'profile_picture': 'url-or-null'
                                },
                                'distance': 5.2,
                                'final_price': 2500.0,
                                'lon_start_location': -1.234,
                                'lat_start_location': 5.678,
                                'lon_end_location': -1.456,
                                'lat_end_location': 5.890,
                                'start_location': 'Address A',
                                'end_location': 'Address B',
                                'prestation': 'economy',
                                'mode_of_payments': 'cash',
                                'distance_to_pickup_km': 2.5,
                                'accepted_time': '2026-01-22T08:00:00Z',
                                'start_time': '2026-01-22T08:00:00Z',
                                'end_time': '2026-01-22T08:00:00Z'
                            }
                        ],
                        'filters_applied': {
                            'max_distance_km': 7.0,
                            'max_age_minutes': 30,
                            'prestation_type': 'economy',
                            'total_results': 12,
                            'cutoff_time': '2026-01-22T08:35:57Z'
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Driver location not available',
            'content': {
                'application/json': {
                    'example': {'Message': 'Driver location not available. Please enable location services.'}
                }
            }
        },
        403: {
            'description': 'Vehicle not validated',
            'content': {
                'application/json': {
                    'example': {'Message': 'Your vehicle must be validated to view ride requests'}
                }
            }
        },
        404: {
            'description': 'Driver or vehicle not found',
            'content': {
                'application/json': {
                    'examples': {
                        'driver_not_found': {'value': {'Message': 'Driver does not exist'}},
                        'vehicle_not_found': {'value': {'Message': 'No vehicle registered for this driver'}}
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_rides_pending(request: Request, *args, **kwargs):
    from math import radians, sin, cos, sqrt, atan2
    from navigation.models import Position
    from datetime import timedelta
    
    _ , driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        driver = Drivers.objects.get(id=driver_decode.id)
    except Drivers.DoesNotExist:
        content = {"Message": "Driver does not exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    # Check if driver has validated vehicle
    try:
        vehicle = Vehicle.objects.get(driver_id=driver.id)
        if vehicle.validation_status != "validated":
            content = {"Message": "Your vehicle must be validated to view ride requests"}
            return Response(data=content, status=status.HTTP_403_FORBIDDEN)
        driver_prestation = vehicle.prestation  # Get driver's vehicle type
    except Vehicle.DoesNotExist:
        content = {"Message": "No vehicle registered for this driver"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    # Get driver's current location
    driver_position = Position.objects.filter(user_id=driver.id).order_by('-timestamp').first()
    if not driver_position:
        content = {"Message": "Driver location not available. Please enable location services."}
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
    
    driver_lat = driver_position.lat
    driver_lon = driver_position.lon
    
    # Get filter parameters from query params
    max_distance_km = request.GET.get('max_distance', None)
    if max_distance_km is not None:
        max_distance_km = float(max_distance_km)
    else:
        max_distance_km = 7.0  # Default 20km radius
    
    limit = int(request.GET.get('limit', 50))  # Default 50 rides max
    max_age_minutes = int(request.GET.get('max_age_minutes', 30))  # Default 30 minutes
    
    # Calculate cutoff time for old requests
    cutoff_time = timezone.now() - timedelta(minutes=max_age_minutes)
    
    # Filter pending rides by prestation type, matching driver's vehicle, and recent requests only
    rides_pending = Rides.objects.filter(
        status='pending',
        prestation=driver_prestation,  # Only show rides matching driver's vehicle type
        start_time__gte=cutoff_time  # Only show rides created within the time window
    ).order_by('-start_time')[:limit * 2]  # Get more than needed for distance filtering
    
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates using Haversine formula (in km)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
    
    # Filter by distance and build response
    serializer_data = []
    for ride in rides_pending:
        # Calculate distance from driver to ride pickup location
        distance_to_pickup = calculate_distance(
            driver_lat, driver_lon,
            ride.lat_start_location, ride.lon_start_location
        )
        
        # Only include rides within max_distance radius
        if distance_to_pickup <= max_distance_km:
            client = ride.client_id  
            profile_picture = client.profile_picture.url if client.profile_picture else None
            if profile_picture:
                profile_picture = request.build_absolute_uri(profile_picture)

            serializer_data.append({
                'id': ride.id,
                'full_name': f"{client.first_name} {client.last_name}",
                'client_details': {
                    'id': client.id,
                    'first_name': client.first_name,
                    'last_name': client.last_name,
                    'email': client.email,
                    'profile_picture': profile_picture, 
                },
                'distance': ride.distance,
                'final_price': ride.final_price,
                'lon_start_location': ride.lon_start_location,
                'lon_end_location': ride.lon_end_location,
                'lat_start_location': ride.lat_start_location,
                'lat_end_location': ride.lat_end_location,
                'start_location': ride.start_location,
                'end_location': ride.end_location,
                'accepted_time': ride.accepted_time,
                'start_time': ride.start_time,
                'end_time': ride.end_time,
                'prestation': ride.prestation,
                'mode_of_payments': ride.mode_of_payments,
                'distance_to_pickup_km': round(distance_to_pickup, 2),  # Distance from driver to pickup
            })
            
            # Stop if we've reached the limit
            if len(serializer_data) >= limit:
                break
    
    # Sort by distance to pickup (closest first)
    serializer_data.sort(key=lambda x: x['distance_to_pickup_km'])

    content = {
        "Message": "Rides in Pending", 
        "Data": serializer_data,
        "filters_applied": {
            "max_distance_km": max_distance_km,
            "max_age_minutes": max_age_minutes,
            "prestation_type": driver_prestation,
            "total_results": len(serializer_data),
            "cutoff_time": cutoff_time.isoformat()
        }
    }
    return Response(data=content, status=status.HTTP_200_OK)



# ------------------------------------ History ------------------------------------------




@extend_schema(
    tags=['History'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
def get_all_driver_rides_history(request: Request, *args, **kwargs): 
    _, driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    try: 
        driver = Drivers.objects.get(id=driver_decode.id)
    except Drivers.DoesNotExist: 
        content = {"Message": "Driver Does Not Exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    all_rides_by_drivers = Rides.objects.filter(driver_id=driver, status="completed").order_by('-end_time')
    sum_gain_all_rides_by_drivers = all_rides_by_drivers.aggregate(Sum('final_price'))['final_price__sum'] or 0 
   
    serializer_data = []
    
    for rides in all_rides_by_drivers:
        # Format date/heure
        ride_date = rides.end_time.strftime('%d %b %Y, %H:%M') if rides.end_time else None
        ride_timestamp = rides.end_time.isoformat() if rides.end_time else None
        
        serializer_data.append({
            'id': rides.id, 
            'full_name': f"{rides.client_id.first_name} {rides.client_id.last_name}", 
            'distance': rides.distance, 
            'final_price': rides.final_price, 
            'start_location': rides.start_location, 
            'end_location': rides.end_location,
            'ride_date': ride_date,
            'timestamp': ride_timestamp,
            'accepted_time': rides.accepted_time.isoformat() if rides.accepted_time else None,
            'start_time': rides.start_time.isoformat() if rides.start_time else None,
            'end_time': rides.end_time.isoformat() if rides.end_time else None, 
            'image_profile': request.build_absolute_uri(rides.client_id.profile_picture.url) if rides.client_id.profile_picture else None,
        })
    
    content = {
        "Message": "Rides History",
        "Data": {
            "History": serializer_data,
            "Total Gains": sum_gain_all_rides_by_drivers
        }
    }
    return Response(data=content, status=status.HTTP_200_OK)
    
    
    
    



@extend_schema(
    tags=['History'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
def get_all_client_ride_history(request: Request, *args, **kwargs): 
    from drivers.models import DriverGrade
    from rides.models import ReviewRating
    from django.db.models import Avg
    
    _, users = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    
    try: 
        client = Clients.objects.get(id=users.id)
    except Clients.DoesNotExist: 
        content = {"Message": "Client Does Not Exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    all_rides_by_client = Rides.objects.filter(client_id=client, status="completed").order_by('-end_time')
    sum_gain_all_rides_by_client = all_rides_by_client.aggregate(Sum('final_price'))['final_price__sum'] or 0 
   
    serializer_data = []
    
    for rides in all_rides_by_client:
        driver = rides.driver_id
        
        # Format date/heure
        ride_date = rides.end_time.strftime('%d %b %Y, %H:%M') if rides.end_time else None
        ride_timestamp = rides.end_time.isoformat() if rides.end_time else None
        
        # Grade du chauffeur
        driver_grade = DriverGrade.objects.filter(
            driver=driver,
            is_current=True
        ).select_related('grade').first()
        grade_name = driver_grade.grade.name if driver_grade else 'Standard'
        
        # Note moyenne du chauffeur
        avg_rating = ReviewRating.objects.filter(driver_id=driver).aggregate(
            avg=Avg('rating')
        )['avg']
        rating = round(float(avg_rating), 1) if avg_rating else 0.0
        
        serializer_data.append({
            'id': rides.id, 
            'full_name': f"{driver.first_name} {driver.last_name}", 
            'distance': rides.distance, 
            'final_price': rides.final_price, 
            'start_location': rides.start_location, 
            'end_location': rides.end_location,
            'prestation': rides.prestation,
            'ride_date': ride_date,
            'timestamp': ride_timestamp,
            'accepted_time': rides.accepted_time.isoformat() if rides.accepted_time else None,
            'start_time': rides.start_time.isoformat() if rides.start_time else None,
            'end_time': rides.end_time.isoformat() if rides.end_time else None,
            'driver_grade': grade_name,
            'driver_rating': rating,
            'image_profile': request.build_absolute_uri(driver.profile_picture.url) if driver.profile_picture else None,
        })
    
    content = {
        "Message": "Rides History",
        "Data": {
            "History": serializer_data,
            "Total expenses": sum_gain_all_rides_by_client
        }
    }
    return Response(data=content, status=status.HTTP_200_OK)
    
    
    
    


@extend_schema(
      tags=['History'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
def get_driver_rides_details(request:Request, rides_id:str  ,  *args, **kwargs) : 
    _ , driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    try : 
        driver = Drivers.objects.get(id = driver_decode.id)
        try : 
            rides_details =Rides.objects.filter(id = rides_id)
            
            serializer_data = []

            for rides in rides_details : 
                serializer_data.append({
                    'id': rides.id, 
                    'full_name':f"{rides.client_id.first_name} {rides.client_id.last_name}  ", 
                    'distance' : rides.distance , 
                    'final_price' : rides.final_price, 
                    'start_location' : rides.start_location , 
                    'end_location' : rides.end_location, 
                    'accepted_time': rides.accepted_time,
                    'start_time': rides.start_time,
                    'end_time': rides.end_time,
                    'image_profile': request.build_absolute_uri(rides.client_id.profile_picture.url)  if rides.client_id.profile_picture else None,
                    
                })
            
            content = {"Message":"Details History","Data":{"Data":serializer_data}}

        except Rides.DoesNotExist : 
            content = {"Message":"Rides Does Not Exist"}
            return Response(data=content , status=status.HTTP_404_NOT_FOUND)
            
    except Drivers.DoesNotExist : 
        content = {"Message":"Drivers Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    
    return Response(data=content , status=status.HTTP_200_OK)
    
   




@extend_schema(
      tags=['History'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
def get_client_rides_details(request:Request, rides_id:str  ,  *args, **kwargs) : 
    _ , users = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    try : 
        client = Clients.objects.get(id = users.id)
        try : 
            rides_details =Rides.objects.filter(id = rides_id)
            
            serializer_data = []

            for rides in rides_details : 
                serializer_data.append({
                    'id': rides.id, 
                    'full_name':f"{rides.driver_id.first_name} {rides.driver_id.last_name}  ", 
                    'distance' : rides.distance , 
                    'final_price' : rides.final_price , 
                    'start_location' : rides.start_location , 
                    'end_location' : rides.end_location, 
                    'accepted_time': rides.accepted_time,
                    'start_time': rides.start_time,
                    'end_time': rides.end_time,
                    'image_profile': request.build_absolute_uri(rides.driver_id.profile_picture.url)  if rides.driver_id.profile_picture else None,

                })
            
            content = {"Message":"Details History","Data":{"Data":serializer_data}}

        except Rides.DoesNotExist : 
            content = {"Message":"Rides Does Not Exist"}
            return Response(data=content , status=status.HTTP_404_NOT_FOUND)
            
    except Drivers.DoesNotExist : 
        content = {"Message":"Drivers Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    
    return Response(data=content , status=status.HTTP_200_OK)






# ------------------------------------ ReviewRating ------------------------------------------

@extend_schema(
      tags=['Rides'], 
    request=ReviewRatingSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_create_review_rating(request:Request  , *args, **kwargs) : 
    
    token , client_decode = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    reviewsRationData = request.data 
    
    rides_id = request.data.get('rides_id', None)
    
    if rides_id : 
        try : 
            rides = Rides.objects.get(id= rides_id)
        except Rides.DoesNotExist : 
            content = {"Message":"Rides Does Not Exist"}
            return Response(data=content , status=status.HTTP_404_NOT_FOUND)
        
    
    serializer = ReviewRatingSerializer(data = reviewsRationData)
    if serializer.is_valid(): 
        data = serializer.save()
        
        client = Clients.objects.get(id = client_decode.id)
        drivers = Drivers.objects.get(id = str(rides.driver_id ))
        send_notification_with_push(

            sender=client,

            recipient=drivers,

            notification_type='new_review',

            message_key='new_review',

            event_id=rides.id

        )

       
        content = {"Message":"Reviews Rating  Was Created"}
        return Response(data=content , status=status.HTTP_200_OK)        
        
    
    content = {"Message":serializer.errors}
    return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
    




@extend_schema(
      tags=['Rides'], 
    request=ReviewRatingSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def drivers_create_review_rating(request:Request  , *args, **kwargs) : 
    
    token , driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    reviewsRationData = request.data 
    
    rides_id = request.data.get('rides_id', None)
    client_id = request.data.get('client_id', None)
    
    if rides_id : 
        try : 
            rides = Rides.objects.get(id= rides_id)
            if client_id : 
                try : 
                    client = Clients.objects.get(id= client_id)
                except Rides.DoesNotExist : 
                    content = {"Message":"Clients Does Not Exist"}
                    return Response(data=content , status=status.HTTP_404_NOT_FOUND)
                
        except Rides.DoesNotExist : 
            content = {"Message":"Rides Does Not Exist"}
            return Response(data=content , status=status.HTTP_404_NOT_FOUND)
        
    
    serializer = ReviewRatingSerializer(data = reviewsRationData)
    
    if serializer.is_valid(): 
        data = serializer.save()
        
        drivers = Drivers.objects.get(id = str(rides.driver_id ))
        send_notification_with_push(

            sender=drivers,

            recipient=client,

            notification_type='new_review',

            message_key='new_review',

            event_id=rides.id

        )
                
        content = {"Message":"Reviews Rating  Was Created"}
        return Response(data=content , status=status.HTTP_200_OK)        
        
    
    content = {"Message":serializer.errors}
    return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
    



















@extend_schema(
      tags=['Rides'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_get_all_review_rating(request:Request ,  *args, **kwargs) : 
    token , driver_decode = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        driver = Drivers.objects.get(id = driver_decode.id) 
    except ReviewRating.DoesNotExist : 
        content = {"Message":"Drivers Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    
    all_review_rating = ReviewRating.objects.filter(driver_id = driver)
    
    mean_of_all_review_rating = all_review_rating.aggregate(Avg('rating'))  ['rating__avg'] or 0 
    
    serializer = ReviewRatingSerializer(all_review_rating , many=True) 
    
    content = {"Message":"Riviews Rating  History", "Average Rating": mean_of_all_review_rating , "Data":serializer.data }
    return Response(data=content , status=status.HTTP_200_OK)



@extend_schema(
    tags=['Rides'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def accepted_driver(request, rides_id: str, *args, **kwargs):
    """
    View to display the driver who accepted a ride.
    Filters rides with status 'accepted_by_driver' and displays information 
    about the driver and the ride.
    """
    token, driver_decode = JWT_FOR_ALL().filter_and_decode_token(request.headers.get("Authorization"))

    try:
        rides = Rides.objects.get(id=rides_id)
    except Rides.DoesNotExist:
        content = {"Message": "Ride does not exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    try:
        vehicle = Vehicle.objects.get(driver_id = rides.driver_id)
    except Vehicle.DoesNotExist:
        content = {"Message": "Driver has not verified their account yet"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)

    # Photo profil chauffeur
    profile_picture = rides.driver_id.profile_picture.url if rides.driver_id.profile_picture else None
    if profile_picture:
        profile_picture = request.build_absolute_uri(profile_picture)
    
    # Photo véhicule
    vehicle_photo = vehicle.photos.url if vehicle.photos else None
    if vehicle_photo:
        vehicle_photo = request.build_absolute_uri(vehicle_photo)
    
    if rides.status == "accepted_by_driver":
        content = {
            'Message': "Ride accepted by driver",
            'Driver': {
                'first_name': rides.driver_id.first_name,
                'lastname': rides.driver_id.last_name,
                "vehicle_brand": vehicle.vehicle_brand,
                "vehicle_model":vehicle.vehicle_model , 
                "license_plate":vehicle.license_plate ,
                "vehicle_color": vehicle.vehicle_color,
                "vehicle_photo": vehicle_photo,
                "profile_picture": profile_picture, 
            },
            'Ride': {
                'ride_id': rides.id,
                'driver_id': str(rides.driver_id),
                'start_location': rides.start_location,
                'end_location': rides.end_location,
                'destination': rides.end_location,
                'distance': rides.distance,
                'prestation': rides.prestation,
                'mode_of_payments': rides.mode_of_payments,
                'accepted_time': rides.accepted_time,
                'start_time': rides.start_time,
                'end_time': rides.end_time,
                'price': rides.final_price,
            }
        }
        return Response(data=content, status=status.HTTP_200_OK)
    else:
        content = {"Message": "Ride not yet accepted by a driver"}
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
@extend_schema(
    tags=['Rides'],
    request=None,  
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_profile_for_client(request: Request, drivers_id: str, *args, **kwargs):
    token, user = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        driver = Drivers.objects.get(id=drivers_id)
        rides_by_driver = Rides.objects.filter(driver_id=driver.id).count()
        all_review_rating = ReviewRating.objects.filter(driver_id=driver.id)
        mean_of_all_review_rating = all_review_rating.aggregate(Avg('rating'))['rating__avg'] or 0 

        vehicle = None
        vehicle_photo = None
        try:
            vehicle = Vehicle.objects.get(driver_id=driver.id)
            
            # Photo véhicule
            vehicle_photo = vehicle.photos.url if vehicle.photos else None
            if vehicle_photo:
                vehicle_photo = request.build_absolute_uri(vehicle_photo)
                
        except Vehicle.DoesNotExist:
            content = {"Message": "Driver has not verified their account yet"}

    except Drivers.DoesNotExist:
        content = {"Message": "Driver Not Found"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)

    driver_data = {
        "first_name": driver.first_name,
        "last_name": driver.last_name,
        "phone_number": driver.phone_number,
        "adresse": driver.adresse,
        "referral_code": driver.referral_code,
        "is_available": driver.is_available, 
        "vehicle_brand": vehicle.vehicle_brand if vehicle else None,
        "vehicle_model": vehicle.vehicle_model if vehicle else None,  
        "license_plate": vehicle.license_plate if vehicle else None, 
        "vehicle_color": vehicle.vehicle_color if vehicle else None,
        "vehicle_photo": vehicle_photo,
        "rides_by_driver": rides_by_driver, 
        "mean_of_all_review_rating": mean_of_all_review_rating, 
    }
    content = {"Message": "Driver Profile Information", "Data": driver_data}
    return Response(data=content, status=status.HTTP_200_OK)





@extend_schema(
    tags=['Rides'],
    request=None, 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_profile_for_driver(request: Request, clients_id: str, *args, **kwargs):
    token, user = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))

    try:

        client = Clients.objects.get(id=clients_id)
        #  Photo profil client
        profile_picture = client.profile_picture.url if client.profile_picture else None
        if profile_picture:
            profile_picture = request.build_absolute_uri(profile_picture)

    except Clients.DoesNotExist:
        content = {"Message": "Client Not Found"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)

    client_data = {
        "first_name": client.first_name,
        "last_name": client.last_name,
        "phone_number": client.phone_number,
        "adresse": client.adresse,
        "referral_code": client.referral_code,
        "profile_picture": profile_picture,
    }
    content = {"Message": "Client Profile Information", "Data": client_data}
    return Response(data=content, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Rides'],
    summary="Get driver's active ride",
    description="Returns the current active ride for the driver (if any). Statuses: accepted_by_driver, in_progress",
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_get_current_ride(request):
    """
    Retourne la course active du chauffeur.
    Permet de reprendre une course après fermeture de l'app.
    """
    _, driver = JWT_Drivers.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Chercher une course active
    active_ride = Rides.objects.filter(
        driver_id=driver.id,
        status__in=['accepted_by_driver', 'in_progress']
    ).order_by('-accepted_time').first()
    
    if not active_ride:
        return Response({
            "Message": "No active ride",
            "Data": None
        }, status=status.HTTP_200_OK)
    
    # Récupérer les infos du client
    client = active_ride.client_id
    client_profile_picture = None
    if client.profile_picture:
        client_profile_picture = request.build_absolute_uri(client.profile_picture.url)
    
    # Retourner les détails complets
    ride_data = {
        "ride_id": str(active_ride.id),
        "status": active_ride.status,
        "client": {
            "client_id": str(client.id),
            "full_name": f"{client.first_name} {client.last_name}",
            "phone_number": client.phone_number,
            "profile_picture": client_profile_picture
        },
        "pickup": {
            "location": active_ride.start_location,
            "latitude": active_ride.lat_start_location,
            "longitude": active_ride.lon_start_location
        },
        "destination": {
            "location": active_ride.end_location,
            "latitude": active_ride.lat_end_location,
            "longitude": active_ride.lon_end_location
        },
        "ride_details": {
            "prestation": active_ride.prestation,
            "final_price": float(active_ride.final_price),
            "distance": float(active_ride.distance) if active_ride.distance else 0.0,
            "mode_of_payments": active_ride.mode_of_payments
        },
        "timestamps": {
            "accepted_time": active_ride.accepted_time.isoformat() if active_ride.accepted_time else None,
            "start_time": active_ride.start_time.isoformat() if active_ride.start_time else None,
            "end_time": active_ride.end_time.isoformat() if active_ride.end_time else None
        }
    }
    
    return Response({
        "Message": "Active ride found",
        "Data": ride_data
    }, status=status.HTTP_200_OK)
    
    

@extend_schema(
    tags=['Rides'],
    summary="Get client's active ride",
    description="Returns the current active ride for the client (if any). Statuses: pending, accepted_by_driver, in_progress",
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_get_current_ride(request):
    """
    Retourne la course active du client avec TOUTES les infos chauffeur.
    Permet de reprendre une course après fermeture de l'app.
    """
    from drivers.models import Vehicle, DriverGrade
    from rides.models import ReviewRating
    from django.db.models import Avg
    
    _, client = JWT_Client.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Chercher une course active
    active_ride = Rides.objects.filter(
        client_id=client.id,
        status__in=['pending', 'accepted_by_driver', 'in_progress']
    ).order_by('-accepted_time').first()
    
    if not active_ride:
        return Response({
            "Message": "No active ride",
            "Data": None
        }, status=status.HTTP_200_OK)
    
    # Construire la réponse selon le statut
    ride_data = {
        "ride_id": str(active_ride.id),
        "status": active_ride.status,
        "pickup": {
            "location": active_ride.start_location,
            "latitude": active_ride.lat_start_location,
            "longitude": active_ride.lon_start_location
        },
        "destination": {
            "location": active_ride.end_location,
            "latitude": active_ride.lat_end_location,
            "longitude": active_ride.lon_end_location
        },
        "ride_details": {
            "prestation": active_ride.prestation,
            "final_price": float(active_ride.final_price),
            "distance": float(active_ride.distance) if active_ride.distance else 0.0,
            "mode_of_payments": active_ride.mode_of_payments
        },
        "timestamps": {
            "accepted_time": active_ride.accepted_time.isoformat() if active_ride.accepted_time else None,
            "start_time": active_ride.start_time.isoformat() if active_ride.start_time else None,
            "end_time": active_ride.end_time.isoformat() if active_ride.end_time else None
        }
    }
    
    # Si course acceptée, ajouter infos chauffeur COMPLÈTES
    if active_ride.driver_id and active_ride.status != 'pending':
        driver = active_ride.driver_id
        
        # Photo chauffeur
        driver_profile_picture = None
        if driver.profile_picture:
            driver_profile_picture = request.build_absolute_uri(driver.profile_picture.url)
        
        # Récupérer grade
        driver_grade = DriverGrade.objects.filter(
            driver=driver,
            is_current=True
        ).select_related('grade').first()
        
        grade_name = driver_grade.grade.name if driver_grade else 'Standard'
        
        # Récupérer note moyenne + nombre d'avis
        avg_rating = ReviewRating.objects.filter(driver_id=driver).aggregate(
            avg=Avg('rating')
        )['avg']
        review_count = ReviewRating.objects.filter(driver_id=driver).count()
        
        try:
            vehicle = Vehicle.objects.get(driver_id=driver.id)
            vehicle_photo = None
            if vehicle.photos:
                vehicle_photo = request.build_absolute_uri(vehicle.photos.url)
            
            ride_data["driver"] = {
                "driver_id": str(driver.id),
                "full_name": f"{driver.first_name} {driver.last_name}",
                "phone_number": driver.phone_number,
                "profile_picture": driver_profile_picture,
                "grade": grade_name,
                "rating": round(float(avg_rating), 1) if avg_rating else 0.0,
                "review_count": review_count,
                "vehicle": {
                    "brand": vehicle.vehicle_brand,
                    "model": vehicle.vehicle_model,
                    "color": vehicle.vehicle_color,
                    "license_plate": vehicle.license_plate,
                    "photo": vehicle_photo
                }
            }
        except Vehicle.DoesNotExist:
            ride_data["driver"] = {
                "driver_id": str(driver.id),
                "full_name": f"{driver.first_name} {driver.last_name}",
                "phone_number": driver.phone_number,
                "profile_picture": driver_profile_picture,
                "grade": grade_name,
                "rating": round(float(avg_rating), 1) if avg_rating else 0.0,
                "review_count": review_count
            }
    
    return Response({
        "Message": "Active ride found",
        "Data": ride_data
    }, status=status.HTTP_200_OK)