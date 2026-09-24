from rest_framework import status 
from rest_framework.request import Request 
from rest_framework.response import Response 
from rest_framework.decorators import api_view, permission_classes 
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from core.utils.notifications import send_notification_with_push
from drivers.customs import JWT as JWT_DRIVER
from clients.customs import JWT as JWT_CLIENT
from .models import Position , PositionHistory , NavigationHistory
from .serializers import AvailableDriverSerializer, HotZoneSerializer, LastPositionOfDriver , PositionHistorySerializer
from drivers.models import Drivers
from .customs import RideAssignmentToDriver 
from drivers.serializers import NearbyDriversForARideProfileSerializer
from rides.models import Rides 
from geopy.distance import geodesic
from notifications.models import Notifications
from clients.models import Clients
import time


@extend_schema(
    request={
        'application/json': {
            'properties': {
                'lat': {'type': 'float', 'example': -12.12123},
                'lon': {'type': 'float', 'example':  -77.0364 }, 
                'adress': {'type': 'string', 'example': "Rue 023 Douala Akwa"}
            }
        }
    },
    tags=['Navigation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_driver_location(request: Request, *args, **kwargs): 
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from django.utils import timezone
    
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    position_data = request.data
    position_data['user_id'] = users.id
    
    lat = position_data.get('lat')
    lon = position_data.get('lon')
    
    driver = Drivers.objects.get(id=users.id) 
    
    if not Position.objects.filter(user_id=users.id).exists():
        serializer_position = LastPositionOfDriver(data=position_data)
         
        driver.is_available = True 
        driver.save()
        
        if serializer_position.is_valid(): 
            serializer_position.save()  
            serializer_history_position = PositionHistorySerializer(data=position_data)
            if serializer_history_position.is_valid(): 
                serializer_history_position.save()
            
            # Broadcast to  backoffice if course active
            active_ride = Rides.objects.filter(
                driver_id=driver.id,
                status__in=['accepted_by_driver', 'in_progress']
            ).first()
            
            if active_ride:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'backoffice_notifications',
                    {
                        'type': 'driver_location_update',
                        'ride_id': str(active_ride.id),
                        'driver_id': str(driver.id),
                        'lat': float(lat),
                        'lon': float(lon),
                        'timestamp': timezone.now().isoformat()
                    }
                )
            
            return Response({"Message": "Position was created successfully"}, status=status.HTTP_200_OK)
        
        return Response({"Message": serializer_position.errors}, status=status.HTTP_400_BAD_REQUEST)

    else:
        position_instance = Position.objects.get(user_id=users.id)
        driver.is_available = True 
        driver.save()
        
        serializer_position = LastPositionOfDriver(position_instance, data=position_data)
        
        if serializer_position.is_valid():
            serializer_position.save()
            serializer_history_position = PositionHistorySerializer(data=position_data)
            if serializer_history_position.is_valid():
                serializer_history_position.save()
            
            # Broadcast to  backoffice if course is active
            active_ride = Rides.objects.filter(
                driver_id=driver.id,
                status__in=['accepted_by_driver', 'in_progress']
            ).first()
            
            if active_ride:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'backoffice_notifications',
                    {
                        'type': 'driver_location_update',
                        'ride_id': str(active_ride.id),
                        'driver_id': str(driver.id),
                        'lat': float(lat),
                        'lon': float(lon),
                        'timestamp': timezone.now().isoformat()
                    }
                )
            
            return Response({"Message": "Position was updated successfully"}, status=status.HTTP_200_OK)
        
        return Response({"Message": serializer_position.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Navigation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_drivers_for_a_ride(request:Request ,rides_id:str,  *args, **kwargs): 
    _, users = JWT_CLIENT.filter_and_decode_token(request.headers.get("Authorization"))

    
    rideAssignmentToDriver = RideAssignmentToDriver(rides_id=rides_id)
    
    closest_drivers = rideAssignmentToDriver.launch_rides_assignment_to_driver()

    i = 0 
    nearest_available_drivers = {}
    for driver, distance in closest_drivers:
        driver = Drivers.objects.get(id = str(driver))
        
        serializer = NearbyDriversForARideProfileSerializer( driver)
        
        nearest_available_drivers[f"Driver N-{i+1}"] = serializer.data
        i +=1 
    return Response({"Message": "nearest available drivers" , "Data":nearest_available_drivers}, status=status.HTTP_200_OK) 



@extend_schema(
    tags=['Navigation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pickup(request: Request, rides_id: str, *args, **kwargs): 
    """
    Get itinerary details between driver and ride start location.

    Uses Google Maps API to calculate distance and duration from the driver's
    current position to the ride's pickup point. Sends notifications to the client 
    when the driver is nearby or has arrived.

    Args:
        request (Request): The incoming HTTP request.
        rides_id (str): The ID of the ride.
        lang (str, optional): Language code (e.g., 'en', 'fr') via query or header.

    Returns:
        Response: Itinerary info, or error if ride/driver not found or invalid state.
    """
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))

    try: 
        rides = Rides.objects.get(id=rides_id)    
    except Rides.DoesNotExist:
        content = {"Message": "Rides Does Not Exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)
    
    if rides.status != 'accepted_by_driver':
        return Response({"Message": "Please accept this race"}, status=status.HTTP_400_BAD_REQUEST)
    

    lang = request.GET.get("lang",'fr') 
    
    
    rideAssignmentToDriver = RideAssignmentToDriver(rides_id=str(rides_id))
    all_informations, duration, distance = rideAssignmentToDriver.pickup(users.id , lang=lang)
    
    try:
        driver = Drivers.objects.get(id=users.id)
        last_position = Position.objects.filter(user_id=driver.id).order_by('-id').first()
    except Drivers.DoesNotExist:
        return Response({"Message": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)

    if not last_position:
        return Response({"Message": "Driver location not available"}, status=status.HTTP_400_BAD_REQUEST)


    current_distance = distance
    if  current_distance >= 0.4 and current_distance <= 1.0:
        print(rides.notified_500m)
        
        if not rides.notified_500m:
            # Notification + Push
            send_notification_with_push(
                sender=driver,
                recipient=rides.client_id,
                notification_type='driver_nearby',
                message_key='driver_nearby',
                event_id=rides.id
            )
            rides.notified_500m = True
            rides.save()

    elif current_distance <= 0.05:
        if not rides.notified_arrived:
            # Notification + Push
            send_notification_with_push(
                sender=driver,
                recipient=rides.client_id,
                notification_type='driver_arrived',
                message_key='driver_almost_arrived',
                event_id=rides.id
            )
            rides.notified_arrived = True
            rides.save()

    
    return Response({
        "Message": "All Itinerary",
        "Total distance (Km)": distance,
        "Total duration": duration,
        "Itinerary": all_informations,
    }, status=status.HTTP_200_OK)






    
    
@extend_schema(
    tags=['Navigation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dropoff(request:Request , rides_id:str,  *args, **kwargs): 
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))

    
    try : 
        rides = Rides.objects.get(id = rides_id)    
    except Rides.DoesNotExist :
        content = {"Message":"Rides Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    if rides.status == 'in_progress': 
        
        rideAssignmentToDriver = RideAssignmentToDriver(rides_id=str(rides_id))
        
        all_informations , duration , distance = rideAssignmentToDriver.dropoff(users.id)
        
        return Response({"Message": "All Itinaraire","Total distance (Km)":distance , "Total duration":duration,   "Itinaraire":all_informations}, status=status.HTTP_200_OK)
    else : 
        return Response({"Message": "Please start this race "}, status=status.HTTP_400_BAD_REQUEST) 



@extend_schema(
    tags=['Navigation'],
    responses={200: AvailableDriverSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_drivers_on_map(request: Request, *args, **kwargs):
    """
    Retourne les chauffeurs disponibles autour d'une position client.
    ACCÈS : CLIENT UNIQUEMENT
    
    Query params:
    - lat: latitude du client (obligatoire)
    - lon: longitude du client (obligatoire)
    - radius: rayon de recherche en km (défaut: 5)
    - prestation: filtrage par type (economy/confort/prestige, optionnel)
    """
    from drivers.models import Vehicle, DriverGrade
    from rides.models import ReviewRating
    from geopy.distance import geodesic
    from django.db.models import Avg
    
    # Vérifier que c'est un CLIENT
    _, users = JWT_CLIENT.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer les paramètres
    try:
        client_lat = float(request.GET.get('lat'))
        client_lon = float(request.GET.get('lon'))
    except (TypeError, ValueError):
        return Response(
            {"Message": "Parameters 'lat' and 'lon' are required and must be valid floats"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    radius_km = float(request.GET.get('radius', 5))  # Défaut 5km
    prestation_filter = request.GET.get('prestation', None)
    
    client_position = (client_lat, client_lon)
    
    # 1. Récupérer les chauffeurs disponibles
    available_drivers = Drivers.objects.filter(is_available=True)
    
    # 2. Exclure ceux qui ont une course en cours
    drivers_with_active_rides = Rides.objects.filter(
        status__in=['in_progress', 'accepted_by_driver']
    ).values_list('driver_id', flat=True)
    
    available_drivers = available_drivers.exclude(id__in=drivers_with_active_rides)
    
    # 3. Récupérer les positions et véhicules
    drivers_data = []
    
    for driver in available_drivers:
        # Position du chauffeur
        last_position = Position.objects.filter(user_id=driver.id).order_by('-id').first()
        if not last_position:
            continue
        
        driver_position = (last_position.lat, last_position.lon)
        
        # Calculer la distance
        distance_km = geodesic(client_position, driver_position).kilometers
        
        # Filtrer par rayon
        if distance_km > radius_km:
            continue
        
        # Récupérer le véhicule
        try:
            vehicle = Vehicle.objects.get(driver_id=driver.id)
        except Vehicle.DoesNotExist:
            continue
        
        # Filtrer par prestation si demandé
        if prestation_filter and vehicle.prestation != prestation_filter:
            continue
        
        # Récupérer le grade et la note du chauffeur
        driver_grade = DriverGrade.objects.filter(
            driver=driver, 
            is_current=True
        ).select_related('grade').first()
        
        grade_name = driver_grade.grade.name if driver_grade else 'Standard'
        commission_rate = float(driver_grade.grade.commission_rate) if driver_grade else 15.00
        
        # Calculer la note moyenne
        avg_rating = ReviewRating.objects.filter(driver_id=driver).aggregate(
            avg=Avg('rating')
        )['avg']
        rating = round(float(avg_rating), 1) if avg_rating else 0.0
        
        # Construire les données
        driver_data = {
            'id': driver.id,
            'first_name': driver.first_name,
            'last_name': driver.last_name,
            'phone_number': driver.phone_number,
            'profile_picture': driver.profile_picture,
            'lat': last_position.lat,
            'lon': last_position.lon,
            'vehicle_brand': vehicle.vehicle_brand,
            'vehicle_model': vehicle.vehicle_model,
            'license_plate': vehicle.license_plate,
            'prestation': vehicle.prestation,
            'vehicle_color': vehicle.vehicle_color,
            'grade': grade_name,
            'commission_rate': commission_rate,
            'rating': rating,
            'distance_km': round(distance_km, 2)
        }
        
        drivers_data.append(driver_data)
    
    # Trier par distance croissante
    drivers_data.sort(key=lambda x: x['distance_km'])
    
    from .serializers import AvailableDriverSerializer
    serializer = AvailableDriverSerializer(drivers_data, many=True)
    
    return Response({
        "Message": "Available drivers on map",
        "Count": len(drivers_data),
        "Data": serializer.data
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Navigation'],
    responses={200: HotZoneSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hot_zones(request: Request, *args, **kwargs):
    """
    Retourne les zones chaudes (zones à forte densité de courses en attente).
    ACCÈS : CHAUFFEUR UNIQUEMENT
    
    Query params:
    - city_wide: true/false - Afficher toutes les zones de la ville (défaut: false)
    - time_window: fenêtre temporelle en minutes (défaut: 30, ignoré si city_wide=true)
    - min_rides: nombre minimum de courses pour qu'une zone soit "chaude" (défaut: 3)
    - grid_size: taille de la grille en km (défaut: 1.0)
    """
    from datetime import timedelta
    from django.utils import timezone
    from collections import defaultdict
    import math
    
    # Vérifier que c'est un CHAUFFEUR
    _, users = JWT_DRIVER.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Paramètres
    city_wide = request.GET.get('city_wide', 'false').lower() == 'true'
    time_window_minutes = int(request.GET.get('time_window', 30))
    min_rides_threshold = int(request.GET.get('min_rides', 3))
    grid_size_km = float(request.GET.get('grid_size', 1.0))
    
    # Filtrage conditionnel
    if city_wide:
        # Mode ville entière : TOUTES les courses pending
        pending_rides = Rides.objects.filter(
            status='pending'
        ).values('id', 'lat_start_location', 'lon_start_location')
        time_window_minutes = None  # Pas de limite de temps
    else:
        # Mode proximité : Courses récentes seulement
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        pending_rides = Rides.objects.filter(
            status='pending',
            start_time__gte=time_threshold
        ).values('id', 'lat_start_location', 'lon_start_location')
    
    if not pending_rides:
        return Response({
            "Message": "No hot zones found",
            "Count": 0,
            "Data": []
        }, status=status.HTTP_200_OK)
    
    # Fonction pour convertir coordonnées GPS en cellule de grille
    def get_grid_cell(lat, lon, grid_size_km):
        """
        Convertit lat/lon en identifiant de cellule de grille.
        1 degré de latitude ≈ 111 km
        """
        lat_per_km = 1.0 / 111.0
        lon_per_km = 1.0 / (111.0 * math.cos(math.radians(lat)))
        
        grid_lat = int(lat / (grid_size_km * lat_per_km))
        grid_lon = int(lon / (grid_size_km * lon_per_km))
        
        return (grid_lat, grid_lon)
    
    # Regrouper les courses par cellule de grille
    grid_zones = defaultdict(list)
    
    for ride in pending_rides:
        lat = ride['lat_start_location']
        lon = ride['lon_start_location']
        
        cell = get_grid_cell(lat, lon, grid_size_km)
        grid_zones[cell].append({'lat': lat, 'lon': lon, 'ride_id': ride['id']})
    
    # Construire les zones chaudes
    hot_zones_data = []
    
    for cell, rides_in_cell in grid_zones.items():
        rides_count = len(rides_in_cell)
        
        # Calculer le centre de la zone (moyenne des positions)
        avg_lat = sum(r['lat'] for r in rides_in_cell) / rides_count
        avg_lon = sum(r['lon'] for r in rides_in_cell) / rides_count
        
        # Déterminer le niveau de densité
        if rides_count >= min_rides_threshold * 2:
            density_level = 'high'  # Violet
        elif rides_count >= min_rides_threshold:
            density_level = 'medium'  # Orange (intermédiaire)
        else:
            density_level = 'low'  # Blanc
        
        # Filtrer uniquement les zones avec au moins le seuil minimum
        if rides_count >= min_rides_threshold or density_level in ['medium', 'high']:
            zone_data = {
                'zone_id': f"zone_{cell[0]}_{cell[1]}",
                'center_lat': round(avg_lat, 6),
                'center_lon': round(avg_lon, 6),
                'rides_count': rides_count,
                'density_level': density_level,
                'radius_km': grid_size_km / 2  # Rayon d'affichage suggéré
            }
            hot_zones_data.append(zone_data)
    
    # Trier par nombre de courses (décroissant)
    hot_zones_data.sort(key=lambda x: x['rides_count'], reverse=True)
    
    from .serializers import HotZoneSerializer
    serializer = HotZoneSerializer(hot_zones_data, many=True)
    
    return Response({
        "Message": "Hot zones retrieved successfully",
        "Count": len(hot_zones_data),
        "City_wide": city_wide,
        "Time_window_minutes": time_window_minutes,
        "Data": serializer.data
    }, status=status.HTTP_200_OK)

@extend_schema(
    tags=['Navigation'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def distance_matrix(request:Request , *args, **kwargs): 
    pass 

