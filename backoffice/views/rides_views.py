from rest_framework import status 
from rest_framework.response import Response 
from rest_framework.request import Request 
from rest_framework.decorators import api_view , permission_classes 
from rides.models import Rides , ReviewRating
import re
from drf_spectacular.utils import extend_schema
from ..serializers import RidesSerializer
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg 



@extend_schema(
    tags=['BackOffice Rides'],
    parameters=[
        {
            'name': 'status',
            'in': 'query',
            'description': 'Filter rides by status (pending, accepted_by_driver, in_progress, completed, cancelled)',
            'required': False,
            'schema': {
                'type': 'string',
                'enum': ['pending', 'accepted_by_driver', 'in_progress', 'completed', 'cancelled']
            }
        }
    ],
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_all_rides(request):
    """
    Récupère toutes les courses avec leurs détails.
    
    Query Parameters:
    - status (optional): Filtrer par statut (pending, accepted_by_driver, in_progress, completed, cancelled)
    
    Examples:
    - GET /api/backoffice/rides → Toutes les courses
    - GET /api/backoffice/rides?status=in_progress → Courses en cours uniquement
    - GET /api/backoffice/rides?status=pending → Courses en attente uniquement
    """
    try:
        # Récupérer le paramètre de filtrage
        status_filter = request.GET.get('status', None)
        
        # Filtrer les courses selon le statut si fourni
        if status_filter:
            # Valider que le statut est valide
            valid_statuses = ['pending', 'accepted_by_driver', 'in_progress', 'completed', 'cancelled']
            if status_filter not in valid_statuses:
                return Response(
                    {"Message": f"Invalid status. Valid options: {', '.join(valid_statuses)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            rides = Rides.objects.filter(status=status_filter)
        else:
            rides = Rides.objects.all()
        
        rides_data = []

        for ride in rides:
            try:
                driver = ride.driver_id
                client = ride.client_id

                ratings_queryset = ReviewRating.objects.filter(rides_id=ride.id)
                if ratings_queryset.exists():
                    ratings = ratings_queryset.aggregate(avg_rating=Avg('rating'))['avg_rating']
                else:
                    ratings = 0

            except ReviewRating.DoesNotExist:
                ratings = 0  
            except Exception as e:
                ratings = 0  

            ride_data = {
                "id": str(ride.id),
                "driver_name": f"{driver.first_name} {driver.last_name}" if driver else "Non spécifié",
                "client_name": f"{client.first_name} {client.last_name}" if client else "Non spécifié",
                "trajectory": f"{ride.start_location} - {ride.end_location}",
                "price_of_ride (FCFA)": ride.final_price,
                "distance_of_ride (Km)": ride.distance,
                "mode_of_payments": ride.mode_of_payments,
                "prestation": ride.prestation,
                "status": ride.status,
                "rating": ratings,
                # Timestamps
                "accepted_time": ride.accepted_time,
                "start_time": ride.start_time,
                "end_time": ride.end_time,
            }

            rides_data.append(ride_data)

        # Informations de filtrage dans la réponse
        message = "Toutes les courses récupérées avec succès"
        if status_filter:
            message = f"Courses filtrées par statut '{status_filter}'"
        
        content = {
            "Message": message,
            "Total": len(rides_data),
            "Filter": {"status": status_filter} if status_filter else None,
            "Data": rides_data
        }
        return Response(data=content, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            data={"Message": f"Erreur lors de la récupération des courses: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['BackOffice Rides'],
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_active_rides(request):
    """
    Récupère uniquement les courses actives (en cours ou acceptées par un chauffeur).
    
    Retourne les courses avec statut 'in_progress' ou 'accepted_by_driver' avec des informations détaillées
    sur le chauffeur, le client, et la position en temps réel du chauffeur.
    
    Useful for monitoring live rides in the backoffice dashboard.
    """
    from navigation.models import Position
    from drivers.models import Vehicle
    
    try:
        # Récupérer les courses actives (acceptées ou en cours)
        active_rides = Rides.objects.filter(
            status__in=['accepted_by_driver', 'in_progress']
        ).order_by('-start_time')
        
        rides_data = []

        for ride in active_rides:
            driver = ride.driver_id
            client = ride.client_id
            
            # Récupérer la position actuelle du chauffeur
            driver_position = None
            if driver:
                last_position = Position.objects.filter(user_id=driver.id).order_by('-timestamp').first()
                if last_position:
                    driver_position = {
                        "lat": last_position.lat,
                        "lon": last_position.lon,
                        "address": last_position.address,
                        "last_update": last_position.timestamp
                    }
            
            # Récupérer les informations du véhicule
            vehicle_info = None
            if driver:
                try:
                    vehicle = Vehicle.objects.get(driver_id=driver.id)
                    vehicle_info = {
                        "brand": vehicle.vehicle_brand,
                        "model": vehicle.vehicle_model,
                        "license_plate": vehicle.license_plate,
                        "color": vehicle.vehicle_color,
                        "prestation": vehicle.prestation
                    }
                except Vehicle.DoesNotExist:
                    pass
            
            # Récupérer la note moyenne du chauffeur
            driver_rating = 0
            if driver:
                ratings_queryset = ReviewRating.objects.filter(driver_id=driver.id)
                if ratings_queryset.exists():
                    driver_rating = ratings_queryset.aggregate(avg_rating=Avg('rating'))['avg_rating']

            ride_data = {
                "id": str(ride.id),
                "status": ride.status,
                "trajectory": f"{ride.start_location} - {ride.end_location}",
                "distance_of_ride (Km)": ride.distance,
                "price_of_ride (FCFA)": ride.final_price,
                "prestation": ride.prestation,
                "mode_of_payments": ride.mode_of_payments,
                
                # Informations chauffeur
                "driver": {
                    "id": str(driver.id) if driver else None,
                    "name": f"{driver.first_name} {driver.last_name}" if driver else "Non assigné",
                    "phone": driver.phone_number if driver else None,
                    "rating": round(driver_rating, 2) if driver_rating else 0,
                    "current_position": driver_position,
                    "vehicle": vehicle_info
                },
                
                # Informations client
                "client": {
                    "id": str(client.id),
                    "name": f"{client.first_name} {client.last_name}",
                    "phone": client.phone_number
                },
                
                # Timestamps
                "accepted_time": ride.accepted_time,
                "start_time": ride.start_time,
            }

            rides_data.append(ride_data)

        content = {
            "Message": "Courses actives récupérées avec succès",
            "Total_Active_Rides": len(rides_data),
            "Data": rides_data
        }
        return Response(data=content, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            data={"Message": f"Erreur lors de la récupération des courses actives: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        

@extend_schema(
    tags=['BackOffice Rides'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_details_of_rides(request:Request , rides_id :str , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        
        rides = Rides.objects.get(id = rides_id)
        driver = rides.driver_id  
        client = rides.client_id
        
        try:
            ratings = ReviewRating.objects.get(rides_id=rides.id).rating
        except ReviewRating.DoesNotExist:
            ratings = 0
        
        ride_data = {
                "id": str(rides.id), 
                "driver_name": f"{driver.first_name} {driver.last_name}" if driver else "Non spécifié",
                "client_name": f"{client.first_name} {client.last_name}" if client else "Non spécifié",
                "trajectory": f"{rides.start_location} - {rides.end_location}",
                "price_of_ride (FCFA)": rides.final_price,
                "distance_of_ride (Km)": rides.distance,
                "status": rides.status,
                "rating": ratings,
            }
           
        
        
    except Exception as e : 
        content  = {"Message":"Rides does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    content = {"Message":'All rides',"Data":ride_data}
    return Response(data=content , status=status.HTTP_200_OK)
    
    
    
@extend_schema(
    tags=['BackOffice Rides'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_rides_request(request:Request,rides_id :str ,  *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        rides = Rides.objects.get(id = rides_id)        
    except Exception as e : 
        content  = {"Message":"Rides does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    if rides.status == "pending" : 
        rides.delete() 
        
        content = {"Message":'This rides has been deleted'}
        return Response(data=content , status=status.HTTP_200_OK)
    
    content  = {"Message":"Impossible to remove this rides as it already belongs to a driver "}
    return Response(data = content , status = status.HTTP_404_NOT_FOUND)