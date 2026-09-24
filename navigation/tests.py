from django.test import TestCase

# Create your tests here.

from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from unittest.mock import patch, MagicMock
import json
import pytest
from django.test import Client as DjangoClient

from navigation.consumers import RideTrackingConsumer
from rides.models import Rides
from clients.models import Clients
from drivers.models import Drivers
from navigation.models import Position

@pytest.fixture
def client():
    """Fixture pour le client Django de test."""
    return DjangoClient()

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestRideTrackingConsumer:
    """
    Test suite for RideTrackingConsumer WebSocket.
    Tests cover connection, authorization, message handling, and real-time updates.
    """
    
    async def setup_test_data(self):
        """Set up test data asynchronously."""
        # Create driver
        self.driver = await database_sync_to_async(Drivers.objects.create)(
            username='testdriver1',
            email='testdriver1@example.com',
            user_type='drivers',
            first_name='Test',
            last_name='Driver',
            phone_number='+2250700000001',
            password='testpass123',
            is_available=True
        )
        
        # Create client
        self.client = await database_sync_to_async(Clients.objects.create)(
            username='testclient1',
            email='testclient1@example.com',
            user_type='client',
            first_name='Test',
            last_name='Client',
            phone_number='+237654542121',
            password='testpass123'
        )
        
        # Create ride
        self.ride = await database_sync_to_async(Rides.objects.create)(
            client_id=self.client,
            driver_id=self.driver,
            start_location='Akwa, Douala',
            end_location='Bonanjo, Douala',
            lat_start_location=4.0511,
            lon_start_location=9.7679,
            lat_end_location=4.0469,
            lon_end_location=9.7631,
            distance=5.2,
            final_price=2500,
            prestation='economy',
            status='accepted_by_driver'
        )
        
        # Create driver position
        self.driver_position = await database_sync_to_async(Position.objects.create)(
            user_id=self.driver,
            lat=4.0580,
            lon=9.7700,
            address='Bali, Douala'
        )
    
    @pytest.mark.asyncio
    @patch('navigation.customs.RideAssignmentToDriver.dropoff')
    async def test_websocket_connect_success(self, mock_dropoff):
        """Test successful WebSocket connection with authorized client."""
        await self.setup_test_data()
        
        # Mock Google Maps API call
        mock_dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        
        # Create communicator
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = self.client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        # Connect
        connected, _ = await communicator.connect()
        assert connected, "WebSocket should connect successfully"
        
        # Should receive initial tracking data
        response = await communicator.receive_json_from()
        assert response['type'] == 'tracking_data'
        assert 'driver_location' in response
        assert 'route_data' in response
        assert response['ride_status'] == 'accepted_by_driver'
        
        # Disconnect
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_connect_unauthorized(self):
        """Test WebSocket connection rejection for unauthorized client."""
        await self.setup_test_data()
        
        # Create another client
        other_client = await database_sync_to_async(Clients.objects.create)(
            username='testclient2',
            email='testclient2@example.com',
            user_type='client',
            first_name='Other',
            last_name='Client',
            phone_number='+237654542122',
            password='testpass123'
        )
        
        # Create communicator with unauthorized user
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = other_client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        # Connect should fail
        connected, close_code = await communicator.connect()
        assert not connected, "WebSocket should reject unauthorized connection"
        assert close_code == 4003, "Should return 4003 (Forbidden)"
    
    @pytest.mark.asyncio
    async def test_websocket_connect_unauthenticated(self):
        """Test WebSocket connection rejection for unauthenticated user."""
        await self.setup_test_data()
        
        # Create communicator without user
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = None
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        # Connect should fail
        connected, close_code = await communicator.connect()
        assert not connected, "WebSocket should reject unauthenticated connection"
        assert close_code == 4001, "Should return 4001 (Unauthorized)"
    
    @pytest.mark.asyncio
    @patch('navigation.customs.RideAssignmentToDriver.dropoff')
    async def test_websocket_receive_refresh_action(self, mock_dropoff):
        """Test refresh action to get updated tracking data."""
        await self.setup_test_data()
        
        # Mock Google Maps API call
        mock_dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = self.client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        await communicator.connect()
        
        # Consume initial message
        await communicator.receive_json_from()
        
        # Send refresh action
        await communicator.send_json_to({
            'action': 'refresh'
        })
        
        # Should receive updated tracking data
        response = await communicator.receive_json_from()
        assert response['type'] == 'tracking_data'
        assert 'driver_location' in response
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    @patch('navigation.customs.RideAssignmentToDriver.dropoff')
    async def test_websocket_receive_ping_action(self, mock_dropoff):
        """Test ping/pong keep-alive mechanism."""
        await self.setup_test_data()
        
        # Mock Google Maps API call
        mock_dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = self.client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        await communicator.connect()
        await communicator.receive_json_from()  # Consume initial message
        
        # Send ping
        await communicator.send_json_to({
            'action': 'ping'
        })
        
        # Should receive pong
        response = await communicator.receive_json_from()
        assert response['type'] == 'pong'
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    @patch('navigation.customs.RideAssignmentToDriver.dropoff')
    async def test_websocket_invalid_json(self, mock_dropoff):
        """Test handling of invalid JSON messages."""
        await self.setup_test_data()
        
        # Mock Google Maps API call
        mock_dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = self.client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        await communicator.connect()
        await communicator.receive_json_from()  # Consume initial message
        
        # Send invalid JSON
        await communicator.send_to(text_data='invalid json{')
        
        # Should receive error message
        response = await communicator.receive_json_from()
        assert response['type'] == 'error'
        assert 'Invalid JSON format' in response['message']
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    @patch('navigation.customs.RideAssignmentToDriver.dropoff')
    async def test_websocket_location_update_broadcast(self, mock_dropoff):
        """Test broadcasting location updates to connected clients."""
        await self.setup_test_data()
        
        # Mock Google Maps API call
        mock_dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = self.client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        await communicator.connect()
        await communicator.receive_json_from()  # Consume initial message
        
        # Simulate location update broadcast
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'ride_tracking_{self.ride.id}',
            {
                'type': 'location_update',
                'driver_location': {
                    'lat': 4.0590,
                    'lon': 9.7710,
                    'address': 'Updated location'
                },
                'timestamp': '2025-01-18T08:00:00Z'
            }
        )
        
        # Should receive location update
        response = await communicator.receive_json_from()
        assert response['type'] == 'location_update'
        assert response['driver_location']['lat'] == 4.0590
        assert response['driver_location']['lon'] == 9.7710
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    @patch('navigation.customs.RideAssignmentToDriver.dropoff')
    async def test_websocket_route_update_broadcast(self, mock_dropoff):
        """Test broadcasting route updates to connected clients."""
        await self.setup_test_data()
        
        # Mock Google Maps API call
        mock_dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = self.client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        await communicator.connect()
        await communicator.receive_json_from()  # Consume initial message
        
        # Simulate route update broadcast
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'ride_tracking_{self.ride.id}',
            {
                'type': 'route_update',
                'route_data': {
                    'route_type': 'dropoff',
                    'total_distance_km': 4.8,
                    'total_duration': '12 mins'
                }
            }
        )
        
        # Should receive route update
        response = await communicator.receive_json_from()
        assert response['type'] == 'route_update'
        assert response['route_data']['total_distance_km'] == 4.8
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_ride_status(self):
        """Test error handling for rides with invalid status."""
        await self.setup_test_data()
        
        # Update ride to pending status
        await database_sync_to_async(lambda: setattr(self.ride, 'status', 'pending'))()
        await database_sync_to_async(self.ride.save)()
        
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = self.client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        await communicator.connect()
        
        # Should receive error message
        response = await communicator.receive_json_from()
        assert response['type'] == 'error'
        assert 'Ride tracking not available' in response['message']
        assert response['ride_status'] == 'pending'
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_no_driver_location(self):
        """Test error handling when driver location is unavailable."""
        await self.setup_test_data()
        
        # Delete driver position
        await database_sync_to_async(Position.objects.filter(user_id=self.driver.id).delete)()
        
        communicator = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator.scope['user'] = self.client
        communicator.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        await communicator.connect()
        
        # Should receive error message
        response = await communicator.receive_json_from()
        assert response['type'] == 'error'
        assert 'Driver location not available' in response['message']
        
        await communicator.disconnect()
    
    @pytest.mark.asyncio
    async def test_websocket_multiple_clients_same_ride(self):
        """Test multiple clients connecting to track the same ride."""
        await self.setup_test_data()
        
        # Create two communicators for the same ride
        communicator1 = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator1.scope['user'] = self.client
        communicator1.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        communicator2 = WebsocketCommunicator(
            RideTrackingConsumer.as_asgi(),
            f'/ws/ride-tracking/{self.ride.id}/'
        )
        communicator2.scope['user'] = self.client
        communicator2.scope['url_route'] = {'kwargs': {'ride_id': str(self.ride.id)}}
        
        # Both should connect successfully
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        
        assert connected1 and connected2, "Both clients should connect"
        
        # Consume initial messages
        await communicator1.receive_json_from()
        await communicator2.receive_json_from()
        
        # Broadcast update
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'ride_tracking_{self.ride.id}',
            {
                'type': 'location_update',
                'driver_location': {'lat': 4.0600, 'lon': 9.7720, 'address': 'Test'},
                'timestamp': '2025-01-18T08:00:00Z'
            }
        )
        
        # Both should receive the update
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()
        
        assert response1['type'] == 'location_update'
        assert response2['type'] == 'location_update'
        
        await communicator1.disconnect()
        await communicator2.disconnect()

# ============================================================================
# TESTS POUR LES ENDPOINTS DE PRIORITÉ 1
# ============================================================================

@pytest.mark.django_db
class TestAvailableDriversEndpoint:
    """
    Test suite for available drivers on map endpoint.
    Tests cover client access, driver filtering, distance calculation, and error handling.
    """
    
    def setup_method(self):
        """Set up test data before each test."""
        # Create drivers
        self.driver1 = Drivers.objects.create(
            username='driver1',
            email='driver1@example.com',
            user_type='drivers',
            first_name='John',
            last_name='Doe',
            phone_number='+2250700000001',
            password='testpass123',
            is_available=True
        )
        
        self.driver2 = Drivers.objects.create(
            username='driver2',
            email='driver2@example.com',
            user_type='drivers',
            first_name='Jane',
            last_name='Smith',
            phone_number='+2250700000002',
            password='testpass123',
            is_available=True
        )
        
        self.driver3 = Drivers.objects.create(
            username='driver3',
            email='driver3@example.com',
            user_type='drivers',
            first_name='Bob',
            last_name='Wilson',
            phone_number='+2250700000003',
            password='testpass123',
            is_available=False  # Offline driver
        )
        
        # Create client
        self.client_user = Clients.objects.create(
            username='testclient',
            email='testclient@example.com',
            user_type='client',
            first_name='Alice',
            last_name='Client',
            phone_number='+237654542121',
            password='testpass123'
        )
        
        # Create vehicles
        from drivers.models import Vehicle
        self.vehicle1 = Vehicle.objects.create(
            driver_id=self.driver1,
            vehicle_model='Toyota Corolla',
            license_plate='ABC-123',
            prestation='economy',
            validation_status='validated'
        )
        
        self.vehicle2 = Vehicle.objects.create(
            driver_id=self.driver2,
            vehicle_model='Mercedes S-Class',
            license_plate='XYZ-789',
            prestation='prestige',
            validation_status='validated'
        )
        
        # Create driver positions (Douala area)
        Position.objects.create(
            user_id=self.driver1,
            lat=4.0511,  # Akwa, Douala
            lon=9.7679,
            address='Akwa, Douala'
        )
        
        Position.objects.create(
            user_id=self.driver2,
            lat=4.0469,  # Bonanjo, Douala (~0.6km from Akwa)
            lon=9.7631,
            address='Bonanjo, Douala'
        )
    
    def test_available_drivers_success(self, client):
        """Test successful retrieval of available drivers."""
        from clients.customs import JWT as JWT_CLIENT
        
        # Generate client token
        tokens = JWT_CLIENT.get_tokens_for_user(self.client_user)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/available-drivers',
            {
                'lat': 4.0500,  # Client position near Akwa
                'lon': 9.7650,
                'radius': 10
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['Message'] == 'Available drivers on map'
        assert data['Count'] == 2  # Only driver1 and driver2 (driver3 is offline)
        assert len(data['Data']) == 2
        
        # Check data structure
        driver_data = data['Data'][0]
        assert 'driver_id' in driver_data
        assert 'first_name' in driver_data
        assert 'lat' in driver_data
        assert 'lon' in driver_data
        assert 'vehicle_model' in driver_data
        assert 'prestation' in driver_data
        assert 'distance_km' in driver_data
    
    def test_available_drivers_filter_by_prestation(self, client):
        """Test filtering drivers by prestation type."""
        from clients.customs import JWT as JWT_CLIENT
        
        tokens = JWT_CLIENT.get_tokens_for_user(self.client_user)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/available-drivers',
            {
                'lat': 4.0500,
                'lon': 9.7650,
                'radius': 10,
                'prestation': 'prestige'
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['Count'] == 1  # Only driver2 with prestige vehicle
        assert data['Data'][0]['prestation'] == 'prestige'
    
    def test_available_drivers_filter_by_radius(self, client):
        """Test filtering drivers by distance radius."""
        from clients.customs import JWT as JWT_CLIENT
        
        tokens = JWT_CLIENT.get_tokens_for_user(self.client_user)
        token = tokens['access']
        
        # Very small radius (should return 0 drivers)
        response = client.get(
            '/api/navigation/available-drivers',
            {
                'lat': 4.0000,  # Far from drivers
                'lon': 9.7000,
                'radius': 0.5
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['Count'] == 0
    
    def test_available_drivers_exclude_busy_drivers(self, client):
        """Test that drivers with active rides are excluded."""
        from clients.customs import JWT as JWT_CLIENT
        
        # Create an active ride for driver1
        Rides.objects.create(
            client_id=self.client_user,
            driver_id=self.driver1,
            start_location='Akwa',
            end_location='Bonanjo',
            lat_start_location=4.0511,
            lon_start_location=9.7679,
            lat_end_location=4.0469,
            lon_end_location=9.7631,
            status='in_progress'
        )
        
        tokens = JWT_CLIENT.get_tokens_for_user(self.client_user)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/available-drivers',
            {
                'lat': 4.0500,
                'lon': 9.7650,
                'radius': 10
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['Count'] == 1  # Only driver2 available (driver1 is busy)
        assert str(data['Data'][0]['driver_id']) == str(self.driver2.id)
    
    def test_available_drivers_missing_params(self, client):
        """Test error handling for missing required parameters."""
        from clients.customs import JWT as JWT_CLIENT
        
        tokens = JWT_CLIENT.get_tokens_for_user(self.client_user)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/available-drivers',
            {'lat': 4.0500},  # Missing 'lon'
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 400
        assert 'lat' in response.json()['Message'] or 'lon' in response.json()['Message']
    
    def test_available_drivers_driver_cannot_access(self, client):
        """Test that drivers cannot access this endpoint (client-only)."""
        from drivers.customs import JWT as JWT_DRIVER
        
        # Try with driver token
        tokens = JWT_DRIVER.get_tokens_for_user(self.driver1)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/available-drivers',
            {
                'lat': 4.0500,
                'lon': 9.7650,
                'radius': 10
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Should fail with authentication error
        assert response.status_code in [401, 403]
    
    def test_available_drivers_no_token(self, client):
        """Test unauthorized access without token."""
        response = client.get(
            '/api/navigation/available-drivers',
            {
                'lat': 4.0500,
                'lon': 9.7650,
                'radius': 10
            }
        )
        
        assert response.status_code == 401


@pytest.mark.django_db
class TestHotZonesEndpoint:
    """
    Test suite for hot zones endpoint.
    Tests cover driver access, zone aggregation, density calculation, and error handling.
    """
    
    def setup_method(self):
        """Set up test data before each test."""
        # Create driver
        self.driver = Drivers.objects.create(
            username='testdriver',
            email='testdriver@example.com',
            user_type='drivers',
            first_name='John',
            last_name='Driver',
            phone_number='+2250700000001',
            password='testpass123',
            is_available=True
        )
        
        # Create client
        self.client_user = Clients.objects.create(
            username='testclient',
            email='testclient@example.com',
            user_type='client',
            first_name='Test',
            last_name='Client',
            phone_number='+237654542121',
            password='testpass123'
        )
        
        # Create multiple pending rides in the same area (Akwa, Douala)
        from django.utils import timezone
        
        for i in range(5):
            Rides.objects.create(
                client_id=self.client_user,
                start_location=f'Akwa Location {i}',
                end_location='Bonanjo',
                lat_start_location=4.0511 + (i * 0.0001),  # Slightly different positions
                lon_start_location=9.7679 + (i * 0.0001),
                lat_end_location=4.0469,
                lon_end_location=9.7631,
                status='pending',
                start_time=timezone.now()
            )
        
        # Create rides in a different area (Bonapriso)
        for i in range(2):
            Rides.objects.create(
                client_id=self.client_user,
                start_location=f'Bonapriso Location {i}',
                end_location='Bonanjo',
                lat_start_location=4.0350 + (i * 0.0001),
                lon_start_location=9.7550 + (i * 0.0001),
                lat_end_location=4.0469,
                lon_end_location=9.7631,
                status='pending',
                start_time=timezone.now()
            )
    
    def test_hot_zones_success(self, client):
        """Test successful retrieval of hot zones."""
        from drivers.customs import JWT as JWT_DRIVER
        
        tokens = JWT_DRIVER.get_tokens_for_user(self.driver)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/hot-zones',
            {
                'time_window': 30,
                'min_rides': 3
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['Message'] == 'Hot zones retrieved successfully'
        assert data['Count'] >= 1  # At least one hot zone (Akwa with 5 rides)
        assert 'Data' in data
        
        # Check hot zone structure
        if data['Count'] > 0:
            zone = data['Data'][0]
            assert 'zone_id' in zone
            assert 'center_lat' in zone
            assert 'center_lon' in zone
            assert 'rides_count' in zone
            assert 'density_level' in zone
            assert zone['density_level'] in ['high', 'medium', 'low']
    
    def test_hot_zones_density_levels(self, client):
        """Test that zones with more rides have higher density levels."""
        from drivers.customs import JWT as JWT_DRIVER
        
        tokens = JWT_DRIVER.get_tokens_for_user(self.driver)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/hot-zones',
            {
                'time_window': 30,
                'min_rides': 2
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Zone with 5 rides should have 'high' density
        # Zone with 2 rides should have 'medium' or 'low' density
        zones_by_count = sorted(data['Data'], key=lambda x: x['rides_count'], reverse=True)
        
        if len(zones_by_count) > 0:
            highest_zone = zones_by_count[0]
            assert highest_zone['rides_count'] >= 5
            assert highest_zone['density_level'] in ['high', 'medium']
    
    def test_hot_zones_no_pending_rides(self, client):
        """Test behavior when no pending rides exist."""
        from drivers.customs import JWT as JWT_DRIVER
        
        # Delete all pending rides
        Rides.objects.filter(status='pending').delete()
        
        tokens = JWT_DRIVER.get_tokens_for_user(self.driver)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/hot-zones',
            {
                'time_window': 30,
                'min_rides': 3
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['Message'] == 'No hot zones found'
        assert data['Count'] == 0
        assert len(data['Data']) == 0
    
    def test_hot_zones_time_window_filter(self, client):
        """Test filtering by time window."""
        from drivers.customs import JWT as JWT_DRIVER
        from django.utils import timezone
        from datetime import timedelta
        
        # Create old rides (beyond time window)
        old_ride = Rides.objects.first()
        old_ride.start_time = timezone.now() - timedelta(hours=2)
        old_ride.save()
        
        tokens = JWT_DRIVER.get_tokens_for_user(self.driver)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/hot-zones',
            {
                'time_window': 30,  # Only last 30 minutes
                'min_rides': 3
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        # Should still find zones (most rides are recent)
    
    def test_hot_zones_client_cannot_access(self, client):
        """Test that clients cannot access this endpoint (driver-only)."""
        from clients.customs import JWT as JWT_CLIENT
        
        # Try with client token
        tokens = JWT_CLIENT.get_tokens_for_user(self.client_user)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/hot-zones',
            {
                'time_window': 30,
                'min_rides': 3
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        # Should fail with authentication error
        assert response.status_code in [401, 403]
    
    def test_hot_zones_no_token(self, client):
        """Test unauthorized access without token."""
        response = client.get(
            '/api/navigation/hot-zones',
            {
                'time_window': 30,
                'min_rides': 3
            }
        )
        
        assert response.status_code == 401
    
    def test_hot_zones_custom_grid_size(self, client):
        """Test custom grid size parameter."""
        from drivers.customs import JWT as JWT_DRIVER
        
        tokens = JWT_DRIVER.get_tokens_for_user(self.driver)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/hot-zones',
            {
                'time_window': 30,
                'min_rides': 2,
                'grid_size': 2.0  # Larger grid (2km)
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Larger grid should potentially merge zones
        assert 'Data' in data
    
    def test_hot_zones_sorted_by_density(self, client):
        """Test that zones are sorted by ride count (descending)."""
        from drivers.customs import JWT as JWT_DRIVER
        
        tokens = JWT_DRIVER.get_tokens_for_user(self.driver)
        token = tokens['access']
        
        response = client.get(
            '/api/navigation/hot-zones',
            {
                'time_window': 30,
                'min_rides': 1
            },
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that zones are sorted by rides_count (descending)
        if len(data['Data']) > 1:
            rides_counts = [zone['rides_count'] for zone in data['Data']]
            assert rides_counts == sorted(rides_counts, reverse=True)
            
# Synchronous tests for compatibility
class RideTrackingConsumerSyncTests(TestCase):
    """Synchronous tests for basic setup validation."""
    
    def test_consumer_exists(self):
        """Test that RideTrackingConsumer is properly defined."""
        from navigation.consumers import RideTrackingConsumer
        self.assertIsNotNone(RideTrackingConsumer)
    
    def test_consumer_has_required_methods(self):
        """Test that consumer has all required methods."""
        from navigation.consumers import RideTrackingConsumer
        
        required_methods = ['connect', 'disconnect', 'receive', 'location_update', 'route_update']
        for method in required_methods:
            self.assertTrue(hasattr(RideTrackingConsumer, method))
