# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class RideTrackingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time ride tracking.
    Clients connect to track a specific ride and receive updates about
    driver location and route information.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.user = self.scope.get('user')
        self.room_group_name = f'ride_tracking_{self.ride_id}'
        
        # Verify user is authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Verify user is authorized to track this ride
        is_authorized = await self.check_authorization()
        if not is_authorized:
            await self.close(code=4003)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial tracking data
        initial_data = await self.get_tracking_data()
        if initial_data:
            await self.send(text_data=json.dumps(initial_data, ensure_ascii=False))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'refresh':
                # Client requests a refresh of tracking data
                tracking_data = await self.get_tracking_data()
                if tracking_data:
                    await self.send(text_data=json.dumps(tracking_data, ensure_ascii=False))
            
            elif action == 'ping':
                # Keep-alive ping
                await self.send(text_data=json.dumps({'type': 'pong'}))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def location_update(self, event):
        """
        Receive location update from channel layer and send to WebSocket.
        This is called when a driver updates their position.
        """
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'driver_location': event['driver_location'],
            'timestamp': event['timestamp']
        }, ensure_ascii=False))
    
    async def route_update(self, event):
        """
        Receive route update from channel layer and send to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'route_update',
            'route_data': event['route_data']
        }, ensure_ascii=False))
    
    @database_sync_to_async
    def check_authorization(self):
        """Check if user is authorized to track this ride."""
        from rides.models import Rides
        
        try:
            ride = Rides.objects.get(id=self.ride_id)
            # User must be the client of this ride
            return str(ride.client_id.id) == str(self.user.id)
        except Rides.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_tracking_data(self):
        """Get current tracking data for the ride."""
        from rides.models import Rides
        from navigation.models import Position
        from navigation.customs import RideAssignmentToDriver
        
        try:
            ride = Rides.objects.get(id=self.ride_id)
            
            # Check ride status
            if ride.status not in ['accepted_by_driver', 'in_progress']:
                return {
                    'type': 'error',
                    'message': 'Ride tracking not available',
                    'ride_status': ride.status
                }
            
            # Check if driver is assigned
            if not ride.driver_id:
                return {
                    'type': 'error',
                    'message': 'No driver assigned'
                }
            
            # Get driver's current location
            driver_position = Position.objects.filter(
                user_id=ride.driver_id.id
            ).order_by('-timestamp').first()
            
            if not driver_position:
                return {
                    'type': 'error',
                    'message': 'Driver location not available'
                }
            
            driver_location = {
                'lat': driver_position.lat,
                'lon': driver_position.lon,
                'address': driver_position.address,
                'timestamp': driver_position.timestamp.isoformat()
            }
            
            # Get route data
            ride_assignment = RideAssignmentToDriver(rides_id=str(self.ride_id))
            
            if ride.status == 'accepted_by_driver':
                # Driver is on the way to pickup
                all_informations, duration, distance = ride_assignment.dropoff(ride.driver_id.id)
                route_type = 'dropoff'
            else:  # in_progress
                # Driver is taking client to destination
                all_informations, duration, distance = ride_assignment.dropoff(ride.driver_id.id)
                route_type = 'dropoff'
            
            return {
                'type': 'tracking_data',
                'ride_status': ride.status,
                'driver_location': driver_location,
                'route_data': {
                    'route_type': route_type,
                    'total_distance_km': distance,
                    'total_duration': duration,
                    'itinerary': all_informations
                }
            }
            
        except Rides.DoesNotExist:
            return {
                'type': 'error',
                'message': 'Ride does not exist'
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': f'Error getting tracking data: {str(e)}'
            }
