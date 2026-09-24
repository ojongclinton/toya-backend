import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class RideStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time ride status updates.
    
    Users (clients and drivers) connect to receive real-time notifications about:
    - Ride acceptance by driver
    - Ride start
    - Ride completion
    - Ride cancellations
    - Any other ride status changes
    
    Connection is user-specific, not ride-specific, allowing users to receive
    updates even before a ride is created or across multiple rides.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')
        
        # Verify user is authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Create a personal channel for this user
        self.user_id = str(self.user.id)
        self.room_group_name = f'ride_updates_{self.user_id}'
        
        # Join personal room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to ride status updates',
            'user_id': self.user_id
        }))
    
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
            
            if action == 'ping':
                # Keep-alive ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif action == 'get_active_rides':
                # Client requests list of their active rides
                active_rides = await self.get_user_active_rides()
                await self.send(text_data=json.dumps({
                    'type': 'active_rides',
                    'rides': active_rides
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def ride_status_update(self, event):
        """
        Receive ride status update from channel layer and send to WebSocket.
        This is called when a ride status changes (accepted, started, completed, cancelled).
        """
        await self.send(text_data=json.dumps({
            'type': 'ride_status_update',
            'ride_id': event['ride_id'],
            'status': event['status'],
            'message': event['message'],
            'timestamp': event.get('timestamp'),
            'data': event.get('data', {})
        }, ensure_ascii=False))
    
    async def ride_accepted(self, event):
        """Specific handler for ride acceptance."""
        await self.send(text_data=json.dumps({
            'type': 'ride_accepted',
            'ride_id': event['ride_id'],
            'driver_id': event.get('driver_id'),
            'driver_name': event.get('driver_name'),
            'accepted_time': event.get('accepted_time'),
            'message': event['message']
        }, ensure_ascii=False))
    
    async def ride_started(self, event):
        """Specific handler for ride start."""
        await self.send(text_data=json.dumps({
            'type': 'ride_started',
            'ride_id': event['ride_id'],
            'start_time': event.get('start_time'),
            'message': event['message']
        }, ensure_ascii=False))
    
    async def ride_completed(self, event):
        """Specific handler for ride completion."""
        await self.send(text_data=json.dumps({
            'type': 'ride_completed',
            'ride_id': event['ride_id'],
            'end_time': event.get('end_time'),
            'final_price': event.get('final_price'),
            'message': event['message']
        }, ensure_ascii=False))
    
    async def ride_cancelled(self, event):
        """Specific handler for ride cancellation."""
        await self.send(text_data=json.dumps({
            'type': 'ride_cancelled',
            'ride_id': event['ride_id'],
            'cancelled_by': event.get('cancelled_by'),
            'reason': event.get('reason'),
            'message': event['message']
        }, ensure_ascii=False))
    
    async def wallet_update(self, event):
        """
        Handler for wallet balance updates (deposits, commissions, etc).
        Sends real-time wallet balance changes to the driver.
        """
        await self.send(text_data=json.dumps({
            'type': 'wallet_update',
            'event_type': event['message'].get('event_type'),
            'transaction_id': event['message'].get('transaction_id'),
            'amount': event['message'].get('amount'),
            'balance_before': event['message'].get('balance_before'),
            'balance_after': event['message'].get('balance_after'),
            'payment_method': event['message'].get('payment_method'),
            'timestamp': event['message'].get('timestamp')
        }, ensure_ascii=False))
    
    @database_sync_to_async
    def get_user_active_rides(self):
        """Get all active rides for the current user."""
        from rides.models import Rides
        from clients.models import Clients
        from drivers.models import Drivers
        
        try:
            # Check if user is a client
            try:
                client = Clients.objects.get(id=self.user.id)
                rides = Rides.objects.filter(
                    client_id=client,
                    status__in=['pending', 'accepted_by_driver', 'in_progress']
                ).values('id', 'status', 'start_location', 'end_location', 'final_price')
                return list(rides)
            except Clients.DoesNotExist:
                pass
            
            # Check if user is a driver
            try:
                driver = Drivers.objects.get(id=self.user.id)
                rides = Rides.objects.filter(
                    driver_id=driver,
                    status__in=['accepted_by_driver', 'in_progress']
                ).values('id', 'status', 'start_location', 'end_location', 'final_price')
                return list(rides)
            except Drivers.DoesNotExist:
                pass
            
            return []
        except Exception as e:
            return []
