"""
Tests for the payment settlement functionality, including grade-based commission calculation.
"""
import uuid
import pytest
from django.test import TestCase
from unittest.mock import patch, MagicMock
from decimal import Decimal

from drivers.models import Drivers, Grade, DriverGrade
from clients.models import Clients
from rides.models import Rides
from payments.utils import DriverEarningsSettlement
from payments.models import PaymentsDrivers


class TestDriverEarningsSettlement(TestCase):
    """Test suite for the DriverEarningsSettlement class."""
    
    def setUp(self):
        """Set up test data."""
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
        self.client_user = Clients.objects.create(
            username='testclient1',
            email='testclient1@example.com',
            user_type='client',
            first_name='Test',
            last_name='Client',
            phone_number='+237654542121',
            password='testpass123'
        )

        # Create test grade
        self.grade = Grade.objects.create(
            name='Steel',
            commission_rate=Decimal('18.00'),  # 18% commission
            is_active=True
        )
        
        # Set driver's wallet to have sufficient funds (more than the commission amount)
        self.driver.wallet_money = Decimal('100000.00')  # Sufficient funds for the test
        self.driver.save()
        
        # Create driver grade
        self.driver_grade = DriverGrade.objects.create(
            driver=self.driver,
            grade=self.grade,
            is_current=True
        )
        
        # Create test ride
        self.ride = Rides.objects.create(
            client_id=self.client_user,
            driver_id=self.driver,
            final_price=Decimal('5000.00'),
            status='completed'
        )
        
        # Initialize the settlement service
        self.settlement = DriverEarningsSettlement()
    
    def test_commission_calculation_with_grade(self):
        """Test that commission is correctly calculated based on driver's grade."""
        # For a ride of 5000 FCFA with 18% commission:
        # - Driver should receive 82% of the amount: 5000 * 0.82 = 4100 FCFA
        
        with patch('payments.customs.WalletPayment.retrieve_a_wallet_driver_amount') as mock_wallet:
            self.settlement.execute_driver_settlement(str(self.ride.id))
            
            # Verify wallet was updated with correct amount
            mock_wallet.assert_called_once()
            args, kwargs = mock_wallet.call_args
            
            self.assertEqual(kwargs['final_rides'], Decimal('5000.00'))
            self.assertEqual(kwargs['driver_id'], str(self.driver.id))
            self.assertEqual(kwargs['percentage'], 18)
    
    def test_commission_without_grade_falls_back_to_default(self):
        """Test that default commission is used when driver has no grade."""
        # Remove driver's grade
        self.driver_grade.delete()
        
        with patch('payments.customs.WalletPayment.retrieve_a_wallet_driver_amount') as mock_wallet:
            self.settlement.execute_driver_settlement(str(self.ride.id))
            
            # Verify wallet was updated with default commission (20%)
            args, kwargs = mock_wallet.call_args
            self.assertEqual(kwargs['percentage'], 15)
    
    # def test_invalid_ride_id_handled_gracefully(self):
    #     """Test that invalid ride IDs are handled without raising exceptions."""
    #     with self.assertLogs(level='ERROR') as log:
    #         self.settlement.execute_driver_settlement(uuid.uuid4())
    #         self.assertIn('Error: Ride not found', log.output[0])
    
    def test_payment_record_created(self):
        """Test that payment records are created correctly for driver settlement."""
        initial_count = PaymentsDrivers.objects.count()
        
        # Don't mock retrieve_a_wallet_driver_amount so we can test the actual payment creation
        self.settlement.execute_driver_settlement(str(self.ride.id))
        
        # Verify two payment records were created:
        # 1. ride_payment record for driver's earnings
        # 2. wallet_pay record for the commission
        self.assertEqual(PaymentsDrivers.objects.count(), initial_count + 2)
        
        # Get the created payments
        payments = list(PaymentsDrivers.objects.order_by('-created_at')[:2])
        
        # Verify ride_payment record
        ride_payment = next(p for p in payments if p.payments_type == 'ride_payment')
        self.assertEqual(ride_payment.amount, Decimal('4100.00'))  # 5000 * 0.85 (15% commission)
        self.assertEqual(ride_payment.payments_status, 'completed')
        self.assertEqual(ride_payment.driver_id, self.driver)
        
        # Verify wallet_pay record
        wallet_payment = next(p for p in payments if p.payments_type == 'wallet_pay')
        self.assertEqual(wallet_payment.amount, Decimal('900.00'))  # 5000 * 0.15
        self.assertEqual(wallet_payment.payments_status, 'completed')
        self.assertEqual(wallet_payment.driver_id, self.driver)