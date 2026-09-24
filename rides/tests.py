from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, MagicMock
from uuid import uuid4

from rides.models import Rides
from clients.models import Clients
from drivers.models import Drivers
from navigation.models import Position
from core.models import BaseUser


class ClientTrackRidesTestCase(APITestCase):
    """
    Test suite for the client_track_rides endpoint.
    Tests cover all scenarios: success cases, error cases, and edge cases.
    """

    def setUp(self):
        """Set up test data before each test."""
        # Créer un chauffeur
        self.driver = Drivers.objects.create(
            username='testdriver1',
            email='testdriver1@example.com',
            user_type='drivers',
            first_name='Test',
            last_name='Driver',
            phone_number='+2250700000001',
            password='testpass123',
            is_available=True
        )
        
        # Créer un client pour les courses
        self.client = Clients.objects.create(
            username='testclient1',
            email='testclient1@example.com',
            user_type='client',
            first_name='Test',
            last_name='Client',
            phone_number='+237654542121',
            password='testpass123'
        )
        
        # Create a ride
        self.ride = Rides.objects.create(
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
        self.driver_position = Position.objects.create(
            user_id=self.driver,
            lat=4.0580,
            lon=9.7700,
            address='Bali, Douala'
        )
        
        # Set up API client
        self.api_client = APIClient()
        
        # Force authenticate as client (bypass JWT for tests)
        self.api_client.force_authenticate(user=self.client)
        
        # Mock JWT token for client
        self.client_token = 'mock_client_token'
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    @patch('rides.views.RideAssignmentToDriver')
    def test_track_ride_success_accepted_status(self, mock_ride_assignment, mock_jwt):
        """Test successful tracking of a ride with 'accepted_by_driver' status."""
        # Mock JWT authentication
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Mock RideAssignmentToDriver methods
        mock_instance = MagicMock()
        mock_instance.pickup.return_value = (
            {'mock': 'pickup_data'},
            '8 mins',
            2.1
        )
        mock_instance.dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        mock_ride_assignment.return_value = mock_instance
        
        # Make request
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['Message'], 'Ride tracking information')
        self.assertEqual(response.data['ride_status'], 'accepted_by_driver')
        
        # Check driver location
        self.assertIn('driver_location', response.data)
        self.assertEqual(response.data['driver_location']['lat'], 4.0580)
        self.assertEqual(response.data['driver_location']['lon'], 9.7700)
        
        # Check main route (dropoff)
        self.assertIn('main_route', response.data)
        self.assertEqual(response.data['main_route']['route_type'], 'dropoff')
        self.assertEqual(response.data['main_route']['total_distance_km'], 5.2)
        
        # Pickup route should not be included by default
        self.assertNotIn('pickup_route', response.data)
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    @patch('rides.views.RideAssignmentToDriver')
    def test_track_ride_with_pickup_route_option(self, mock_ride_assignment, mock_jwt):
        """Test tracking with include_pickup_route=true parameter."""
        # Mock JWT authentication
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Mock RideAssignmentToDriver methods
        mock_instance = MagicMock()
        mock_instance.pickup.return_value = (
            {'mock': 'pickup_data'},
            '8 mins',
            2.1
        )
        mock_instance.dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        mock_ride_assignment.return_value = mock_instance
        
        # Make request with parameter
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(f'{url}?include_pickup_route=true')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Pickup route should be included
        self.assertIn('pickup_route', response.data)
        self.assertEqual(response.data['pickup_route']['route_type'], 'pickup')
        self.assertEqual(response.data['pickup_route']['total_distance_km'], 2.1)
        self.assertEqual(response.data['pickup_route']['total_duration'], '8 mins')
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    @patch('rides.views.RideAssignmentToDriver')
    def test_track_ride_in_progress_status(self, mock_ride_assignment, mock_jwt):
        """Test tracking a ride with 'in_progress' status."""
        # Update ride status
        self.ride.status = 'in_progress'
        self.ride.save()
        
        # Mock JWT authentication
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Mock RideAssignmentToDriver
        mock_instance = MagicMock()
        mock_instance.dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '10 mins',
            3.5
        )
        mock_ride_assignment.return_value = mock_instance
        
        # Make request
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ride_status'], 'in_progress')
        self.assertEqual(response.data['main_route']['route_type'], 'dropoff')
        
        # Pickup route should not be available for in_progress rides
        self.assertNotIn('pickup_route', response.data)
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    def test_track_ride_not_found(self, mock_jwt):
        """Test tracking a non-existent ride."""
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Use a random UUID
        fake_ride_id = uuid4()
        url = reverse('client_track_rides', kwargs={'rides_id': str(fake_ride_id)})
        response = self.api_client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['Message'], 'Ride does not exist')
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    def test_track_ride_unauthorized_client(self, mock_jwt):
        """Test that a client cannot track another client's ride."""
        # Create another client
        other_client = Clients.objects.create(
            username='testclient2',
            email='testclient2@example.com',
            user_type='client',
            first_name='Test',
            last_name='Client',
            phone_number='+237654542122',
            password='testpass123'
        )
        
        # Mock JWT for the other client
        mock_jwt.return_value = (self.client_token, other_client)
        
        # Force authenticate as the other client
        self.api_client.force_authenticate(user=other_client)
        
        # Try to track the ride
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(url)
        
        # Reset authentication to original client
        self.api_client.force_authenticate(user=self.client)
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['Message'], 'You are not authorized to track this ride')
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    def test_track_ride_invalid_status(self, mock_jwt):
        """Test tracking a ride with invalid status (pending, completed, cancelled)."""
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Test with 'pending' status
        self.ride.status = 'pending'
        self.ride.save()
        
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Ride tracking not available', response.data['Message'])
        self.assertIn('pending', response.data['reason'])
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    def test_track_ride_no_driver_assigned(self, mock_jwt):
        """Test tracking a ride with no driver assigned."""
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Remove driver from ride
        self.ride.driver_id = None
        self.ride.status = 'pending'
        self.ride.save()
        
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    def test_track_ride_no_driver_location(self, mock_jwt):
        """Test tracking when driver location is not available."""
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Delete driver position
        Position.objects.filter(user_id=self.driver.id).delete()
        
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['Message'], 'Driver location not available')
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    @patch('rides.views.RideAssignmentToDriver')
    def test_track_ride_with_language_parameter(self, mock_ride_assignment, mock_jwt):
        """Test tracking with language parameter (lang=en)."""
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Mock RideAssignmentToDriver
        mock_instance = MagicMock()
        mock_instance.dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        mock_ride_assignment.return_value = mock_instance
        
        # Make request with lang parameter
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(f'{url}?lang=en')
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that dropoff was called with lang='en'
        mock_instance.dropoff.assert_called_once_with(self.driver.id, lang='en')
        
    @patch('rides.views.JWT_Client.filter_and_decode_token')
    @patch('rides.views.RideAssignmentToDriver')
    def test_track_ride_driver_location_timestamp(self, mock_ride_assignment, mock_jwt):
        """Test that driver location includes timestamp."""
        mock_jwt.return_value = (self.client_token, self.client)
        
        # Mock RideAssignmentToDriver
        mock_instance = MagicMock()
        mock_instance.dropoff.return_value = (
            {'mock': 'dropoff_data'},
            '15 mins',
            5.2
        )
        mock_ride_assignment.return_value = mock_instance
        
        # Make request
        url = reverse('client_track_rides', kwargs={'rides_id': str(self.ride.id)})
        response = self.api_client.get(url)
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('timestamp', response.data['driver_location'])
        self.assertIsNotNone(response.data['driver_location']['timestamp'])
