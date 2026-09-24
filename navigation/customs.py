from drivers.models import Drivers 
from .models import Position
from .localisation import GoogleMaps
from rides.models import Rides
from notifications.models import Notifications
from notifications.custums import RetrieveBackofficeUser
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import math
from core.utils.translations import get_message
from core.utils.language import get_user_language
# import googlemaps
# from dotenv import load_dotenv 
# import os 

# load_dotenv()
# GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')




# gmaps = googlemaps.Client(key=GOOGLE_API_KEY)


class RideAssignmentToDriver: 
    def __init__(self, rides_id:str) -> None:
        self.rides_id = rides_id 
    
    
    def fetch_nearest_available_drivers(self,) : 
        driver = Drivers.objects.filter(is_available = True)
        
        return driver
    
    
    def get_current_driver_positions(self, available_drivers) : 
        driver_positions = {}
        for driver in available_drivers:
            last_position = Position.objects.filter(user_id=driver.id).order_by('-id').first()
            if last_position:
                driver_positions[driver] = (last_position.lat, last_position.lon)
                
        return driver_positions 
    
    def distance_calculation(self, driver_positions):
        rides = Rides.objects.get(id=str(self.rides_id))
        start_location = (rides.lat_start_location, rides.lon_start_location)
        
        distances = []
        for driver, position in driver_positions.items():
            driver_location = position
            distance = None  

            try:
                data = GoogleMaps().calcul_distance_beetween_localisation(
                    rides_source=start_location, driver_source=driver_location
                )


                distance = data["distance"]
                duration = data["duration"]


            except Exception as e:
                print(f"Error calculating distance for driver {driver}: {e}")
                distance = 'Error'  

            distances.append((driver, distance)) 

        return distances
    
    
    

    def select_the_best_nearest_drivers(self, distances, number_of_driver=15):
        valid_distances = [
            (driver, float(distance)) 
            for driver, distance in distances 
            if isinstance(distance, str) and distance.replace('.', '', 1).isdigit()  
        ]
        
        valid_distances.sort(key=lambda x: x[1])
        
        closest_drivers = valid_distances[:number_of_driver]
      
        return closest_drivers


        
    def send_ride_to_select_driver(self,closest_drivers ) : 
        for driver, distance in closest_drivers:
        
            
            user_id = RetrieveBackofficeUser().retrieve_backoffice_user(driver)
            notifications = Notifications.objects.create( 
                                                    sender = user_id , 
                                                    recipient = driver, 
                                                    notification_type ='new_ride', 
                                                    message=get_message("new_ride_available", get_user_language)
                                                    )
            notifications.save()
            
        return 0  
    
    
    def launch_rides_assignment_to_driver(self) : 
        all_drivers = self.fetch_nearest_available_drivers()
        
        all_drivers_positions = self.get_current_driver_positions(all_drivers)

        all_drivers_positions_with_rides_pos_request = self.distance_calculation(all_drivers_positions)
        
        closest_drivers = self.select_the_best_nearest_drivers(all_drivers_positions_with_rides_pos_request)
        
        response = self.send_ride_to_select_driver(closest_drivers)
        
        return closest_drivers
    
    
    def pickup(self, driver_id, lang='fr'):
        """Pickup (Récupération du client)"""

        driver = Drivers.objects.get(id=driver_id)
        driver_positions = {}
        last_position = Position.objects.filter(user_id=driver.id).order_by('-id').first()
        if last_position:
            driver_positions[driver] = (last_position.lat, last_position.lon)

        rides = Rides.objects.get(id=str(self.rides_id))
        start_location = (rides.lat_start_location, rides.lon_start_location)

        for driver, position in driver_positions.items():
            driver_location = position

        try:
            data = GoogleMaps().calcul_distance_beetween_localisation(driver_location, start_location, language=lang)
            
            #  VÉRIFICATION
            if data is None:
                return None, None, None
            
            distance = data.get("distance")
            duration = data.get("duration")
            raw_data = data.get("raw_data")
            
            return raw_data, duration, distance
            
        except Exception as e:
            print(f"Error in pickup calculation: {e}")
            return None, None, None


    def dropoff(self, driver_id, lang='fr'):
        """
        Dropoff (Déposer le client)
        """
        rides = Rides.objects.get(id=str(self.rides_id))

        start_location = (rides.lat_start_location, rides.lon_start_location)
        end_location = (rides.lat_end_location, rides.lon_end_location)

        try:
            data = GoogleMaps().calcul_distance_beetween_localisation(start_location, end_location, language=lang)
            
            # VÉRIFICATION
            if data is None:
                return None, None, None
            
            distance = data.get("distance")
            duration = data.get("duration")
            raw_data = data.get("raw_data")
            
            return raw_data, duration, distance
            
        except Exception as e:
            print(f"Error in dropoff calculation: {e}")
            return None, None, None


            return raw_data, duration, distance



def notify_nearby_drivers(ride_id, pickup_lat, pickup_lon, prestation, radius_km=10):
    """
    Envoie une notification aux chauffeurs disponibles dans un rayon donné.
    """
    from drivers.models import Vehicle
    
    ride = Rides.objects.get(id=ride_id)
    available_drivers = Drivers.objects.filter(is_available=True)
    backoffice_user = RetrieveBackofficeUser().retrieve_backoffice_user(ride.client_id.id)
    
    notified_count = 0
    channel_layer = get_channel_layer()
    
    for driver in available_drivers:
        # Vérifier véhicule
        try:
            vehicle = Vehicle.objects.get(
                driver_id=driver.id,
                validation_status='validated',
                prestation=prestation
            )
        except Vehicle.DoesNotExist:
            continue
        
        # Vérifier position
        try:
            driver_position = Position.objects.filter(
                user_id=driver.id
            ).order_by('-timestamp').first()
            
            if not driver_position:
                continue
        except Position.DoesNotExist:
            continue
        
        # UTILISER HAVERSINE (rapide) au lieu de GoogleMaps
        distance = haversine_distance(
            pickup_lat, pickup_lon,
            driver_position.lat, driver_position.lon
        )
        
        if distance <= radius_km:
            # Créer notification
            notification = Notifications.objects.create(
                sender=backoffice_user,
                recipient=driver,
                notification_type='course_available',
                message=get_message("course_available", get_user_language, distance=f"{distance:.1f}", price=ride.final_price),
                event_id=str(ride.id)
            )
            
            # WebSocket
            async_to_sync(channel_layer.group_send)(
                f'ride_updates_{driver.id}',
                {
                    'type': 'new_ride_available',
                    'message': {
                        'ride_id': str(ride.id),
                        'pickup': ride.start_location,
                        'destination': ride.end_location,
                        'distance_from_you': round(distance, 1),
                        'price': float(ride.final_price),
                        'prestation': ride.prestation,
                        'notification_id': str(notification.id),
                        'timestamp': notification.timestamp.isoformat()
                    }
                }
            )
            
            notified_count += 1
    
    print(f"{notified_count} chauffeurs notifiés pour la course {ride_id}")
    return notified_count


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en km entre deux points GPS (formule de Haversine).
    RAPIDE - pas d'appel API.
    """
    R = 6371  # Rayon de la Terre en km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c
