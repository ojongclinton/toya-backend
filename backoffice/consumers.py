import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class BackofficeConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer pour le backoffice.
    Reçoit les notifications temps réel sur toutes les activités du système.
    """
    
    async def connect(self):
        """Connexion au WebSocket backoffice"""
        # Groupe unique pour tous les admins du backoffice
        self.group_name = 'backoffice_notifications'
        
        # Rejoindre le groupe backoffice
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer message de confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to backoffice notifications'
        }))
    
    async def disconnect(self, close_code):
        """Déconnexion du WebSocket"""
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    # Handlers pour chaque type d'événement
    
    async def ride_created(self, event):
        """Nouvelle course créée"""
        await self.send(text_data=json.dumps({
            'type': 'ride_created',
            'ride_id': event['ride_id'],
            'client_name': event['client_name'],
            'pickup_location': event['pickup_location'],
            'destination': event['destination'],
            'prestation': event['prestation'],
            'price': event['price'],
            'timestamp': event['timestamp']
        }))
    
    async def ride_accepted(self, event):
        """Course acceptée par un chauffeur"""
        await self.send(text_data=json.dumps({
            'type': 'ride_accepted',
            'ride_id': event['ride_id'],
            'driver_name': event['driver_name'],
            'driver_id': event['driver_id'],
            'timestamp': event['timestamp']
        }))
    
    async def ride_started(self, event):
        """Course démarrée"""
        await self.send(text_data=json.dumps({
            'type': 'ride_started',
            'ride_id': event['ride_id'],
            'driver_name': event['driver_name'],
            'timestamp': event['timestamp']
        }))
    
    async def ride_completed(self, event):
        """Course terminée"""
        await self.send(text_data=json.dumps({
            'type': 'ride_completed',
            'ride_id': event['ride_id'],
            'driver_name': event['driver_name'],
            'final_price': event['final_price'],
            'commission': event.get('commission'),
            'timestamp': event['timestamp']
        }))
    
    async def ride_cancelled(self, event):
        """Course annulée"""
        await self.send(text_data=json.dumps({
            'type': 'ride_cancelled',
            'ride_id': event['ride_id'],
            'cancelled_by': event['cancelled_by'],
            'reason': event.get('reason', 'Not specified'),
            'timestamp': event['timestamp']
        }))
    
    async def driver_location_update(self, event):
        """Position GPS chauffeur mise à jour (courses actives uniquement)"""
        await self.send(text_data=json.dumps({
            'type': 'driver_location_update',
            'ride_id': event['ride_id'],
            'driver_id': event['driver_id'],
            'lat': event['lat'],
            'lon': event['lon'],
            'timestamp': event['timestamp']
        }))
    
    async def new_driver_registration(self, event):
        """Nouveau chauffeur inscrit"""
        await self.send(text_data=json.dumps({
            'type': 'new_driver_registration',
            'driver_id': event['driver_id'],
            'driver_name': event['driver_name'],
            'phone_number': event['phone_number'],
            'timestamp': event['timestamp']
        }))
    
    async def new_client_registration(self, event):
        """Nouveau client inscrit"""
        await self.send(text_data=json.dumps({
            'type': 'new_client_registration',
            'client_id': event['client_id'],
            'client_name': event['client_name'],
            'phone_number': event['phone_number'],
            'timestamp': event['timestamp']
        }))
    
    async def vehicle_submission(self, event):
        """Véhicule soumis pour validation"""
        await self.send(text_data=json.dumps({
            'type': 'vehicle_submission',
            'driver_id': event['driver_id'],
            'driver_name': event['driver_name'],
            'vehicle_brand': event['vehicle_brand'],
            'vehicle_model': event['vehicle_model'],
            'license_plate': event['license_plate'],
            'timestamp': event['timestamp']
        }))
    
    async def payment_received(self, event):
        """Paiement reçu"""
        await self.send(text_data=json.dumps({
            'type': 'payment_received',
            'payment_id': event['payment_id'],
            'user_type': event['user_type'],
            'amount': event['amount'],
            'payment_method': event['payment_method'],
            'timestamp': event['timestamp']
        }))