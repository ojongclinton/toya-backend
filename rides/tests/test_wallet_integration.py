"""
Integration tests for ride acceptance and completion with wallet management.
Tests cover grade-based commission validation, atomic operations, and error handling.
"""
import pytest
import logging
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from drivers.models import Drivers, Grade, DriverGrade, Vehicle
from clients.models import Clients
from rides.models import Rides
from payments.models import WalletTransaction, PaymentsDrivers
from drivers.customs import JWT as JWT_Drivers

# Configure logging for tests
logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestRideAcceptanceWithWallet(TestCase):
    """Test ride acceptance with grade-based wallet validation."""
    
    def setUp(self):
        """Set up test data with detailed logging."""
        logger.info("=" * 80)
        logger.info("SETTING UP RIDE ACCEPTANCE TESTS")
        logger.info("=" * 80)
        
        self.client_api = APIClient()
        
        # Create grades
        logger.info("Creating test grades...")
        self.bronze_grade = Grade.objects.create(
            name='Bronze',
            commission_rate=Decimal('20.00'),
            is_active=True
        )
        self.gold_grade = Grade.objects.create(
            name='Gold',
            commission_rate=Decimal('18.00'),
            is_active=True
        )
        logger.info(f"✓ Created Bronze ({self.bronze_grade.commission_rate}%) and Gold ({self.gold_grade.commission_rate}%) grades")
        
        # Create driver
        logger.info("\nCreating test driver...")
        self.driver = Drivers.objects.create(
            username='acceptance_driver',
            email='acceptance_driver@example.com',
            user_type='drivers',
            first_name='Acceptance',
            last_name='Driver',
            phone_number='+237600000010',
            password='testpass123',
            wallet_money=Decimal('5000.00'),
            is_available=True
        )
        logger.info(f"✓ Created driver: {self.driver.username}")
        logger.info(f"  Wallet balance: {self.driver.wallet_money} FCFA")
        
        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            driver_id=self.driver,
            vehicle_model='Honda Accord',
            license_plate='ACC-001',
            validation_status='validated'
        )
        logger.info(f"✓ Created validated vehicle: {self.vehicle.license_plate}")
        
        # Assign Bronze grade
        self.driver_grade = DriverGrade.objects.create(
            driver=self.driver,
            grade=self.bronze_grade,
            is_current=True,
            reason="Test assignment"
        )
        logger.info(f"✓ Assigned {self.bronze_grade.name} grade to driver")
        
        # Create client
        logger.info("\nCreating test client...")
        self.client_user = Clients.objects.create(
            username='acceptance_client',
            email='acceptance_client@example.com',
            user_type='client',
            first_name='Acceptance',
            last_name='Client',
            phone_number='+237600000011',
            password='testpass123'
        )
        logger.info(f"✓ Created client: {self.client_user.username}")
        
        # Create pending ride
        logger.info("\nCreating pending ride...")
        self.ride = Rides.objects.create(
            client_id=self.client_user,
            final_price=Decimal('5000.00'),
            status='pending',
            start_location='Location A',
            end_location='Location B'
        )
        logger.info(f"✓ Created ride: {self.ride.id}")
        logger.info(f"  Price: {self.ride.final_price} FCFA")
        logger.info(f"  Status: {self.ride.status}")
        
        logger.info("\n" + "=" * 80)
        logger.info("SETUP COMPLETE")
        logger.info("=" * 80 + "\n")
    
    def test_ride_acceptance_with_sufficient_wallet_bronze_grade(self):
        """Test ride acceptance with sufficient wallet balance (Bronze grade - 20%)."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Ride Acceptance - Sufficient Wallet (Bronze 20%)")
        logger.info("=" * 80)
        
        logger.info(f"Initial State:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Grade: {self.bronze_grade.name} ({self.bronze_grade.commission_rate}%)")
        logger.info(f"  Wallet Balance: {self.driver.wallet_money} FCFA")
        logger.info(f"  Ride Price: {self.ride.final_price} FCFA")
        
        required_commission = (self.ride.final_price * self.bronze_grade.commission_rate) / 100
        logger.info(f"  Required Commission: {required_commission} FCFA")
        logger.info(f"  Can Accept: {self.driver.wallet_money >= required_commission}")
        
        # Authenticate as driver
        self.client_api.force_authenticate(user=self.driver)
        
        # Mock JWT static method to return driver
        with patch('rides.views.JWT_Drivers') as mock_jwt:
            mock_jwt.filter_and_decode_token.return_value = ('fake_token', self.driver)
            logger.info(f"\nAttempting to accept ride...")
            response = self.client_api.get(
                f'/api/rides/driver/{self.ride.id}/accept',
                HTTP_AUTHORIZATION='Bearer fake_token'
            )
        
        logger.info(f"✓ Response received")
        logger.info(f"  Status Code: {response.status_code}")
        logger.info(f"  Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('accepted', response.data['Message'].lower())
        
        # Verify ride status updated
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status, 'accepted_by_driver')
        logger.info(f"\n✓ Ride status updated: {self.ride.status}")
        
        # Verify driver assigned
        self.assertEqual(self.ride.driver_id, self.driver)
        logger.info(f"✓ Driver assigned to ride")
        
        # Verify driver marked unavailable
        self.driver.refresh_from_db()
        self.assertFalse(self.driver.is_available)
        logger.info(f"✓ Driver marked unavailable")
        
        logger.info("\n✓ TEST PASSED: Ride accepted successfully with sufficient wallet")
    
    def test_ride_acceptance_with_insufficient_wallet_bronze_grade(self):
        """Test ride acceptance fails with insufficient wallet balance (Bronze grade - 20%)."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Ride Acceptance - Insufficient Wallet (Bronze 20%)")
        logger.info("=" * 80)
        
        # Set insufficient wallet balance
        insufficient_balance = Decimal('500.00')
        self.driver.wallet_money = insufficient_balance
        self.driver.save()
        
        logger.info(f"Initial State:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Grade: {self.bronze_grade.name} ({self.bronze_grade.commission_rate}%)")
        logger.info(f"  Wallet Balance: {self.driver.wallet_money} FCFA")
        logger.info(f"  Ride Price: {self.ride.final_price} FCFA")
        
        required_commission = (self.ride.final_price * self.bronze_grade.commission_rate) / 100
        logger.info(f"  Required Commission: {required_commission} FCFA")
        logger.info(f"  Shortfall: {required_commission - insufficient_balance} FCFA")
        
        # Authenticate as driver
        self.client_api.force_authenticate(user=self.driver)
        
        # Mock JWT static method to return driver
        with patch('rides.views.JWT_Drivers') as mock_jwt:
            mock_jwt.filter_and_decode_token.return_value = ('fake_token', self.driver)
            logger.info(f"\nAttempting to accept ride...")
            response = self.client_api.get(
                f'/api/rides/driver/{self.ride.id}/accept',
                HTTP_AUTHORIZATION='Bearer fake_token'
            )
        
        logger.info(f"✓ Response received")
        logger.info(f"  Status Code: {response.status_code}")
        logger.info(f"  Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('required_amount', response.data)
        self.assertIn('current_balance', response.data)
        self.assertIn('commission_rate', response.data)
        
        logger.info(f"\n✓ Detailed error response:")
        logger.info(f"  Required Amount: {response.data['required_amount']} FCFA")
        logger.info(f"  Current Balance: {response.data['current_balance']} FCFA")
        logger.info(f"  Commission Rate: {response.data['commission_rate']}%")
        logger.info(f"  Grade: {response.data['grade']}")
        
        # Verify ride status unchanged
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status, 'pending')
        logger.info(f"\n✓ Ride status unchanged: {self.ride.status}")
        
        logger.info("\n✓ TEST PASSED: Insufficient wallet properly rejected")
    
    def test_ride_acceptance_with_gold_grade_lower_commission(self):
        """Test ride acceptance with Gold grade (18% - lower commission required)."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Ride Acceptance - Gold Grade (18% Commission)")
        logger.info("=" * 80)
        
        # Upgrade driver to Gold grade
        logger.info("Upgrading driver to Gold grade...")
        self.driver_grade.is_current = False
        self.driver_grade.save()
        
        DriverGrade.objects.create(
            driver=self.driver,
            grade=self.gold_grade,
            is_current=True,
            reason="Test upgrade to Gold"
        )
        logger.info(f"✓ Driver upgraded to {self.gold_grade.name}")
        
        # Set wallet balance that works for Gold but not Bronze
        # Gold 18% of 5000 = 900 FCFA
        # Bronze 20% of 5000 = 1000 FCFA
        wallet_balance = Decimal('950.00')
        self.driver.wallet_money = wallet_balance
        self.driver.save()
        
        logger.info(f"\nInitial State:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Grade: {self.gold_grade.name} ({self.gold_grade.commission_rate}%)")
        logger.info(f"  Wallet Balance: {self.driver.wallet_money} FCFA")
        logger.info(f"  Ride Price: {self.ride.final_price} FCFA")
        
        required_commission = (self.ride.final_price * self.gold_grade.commission_rate) / 100
        logger.info(f"  Required Commission (Gold): {required_commission} FCFA")
        logger.info(f"  Would Need (Bronze): {(self.ride.final_price * Decimal('20.00')) / 100} FCFA")
        logger.info(f"  Can Accept with Gold: {wallet_balance >= required_commission}")
        
        # Authenticate as driver
        self.client_api.force_authenticate(user=self.driver)
        
        # Mock JWT static method to return driver
        with patch('rides.views.JWT_Drivers') as mock_jwt:
            mock_jwt.filter_and_decode_token.return_value = ('fake_token', self.driver)
            logger.info(f"\nAttempting to accept ride...")
            response = self.client_api.get(
                f'/api/rides/driver/{self.ride.id}/accept',
                HTTP_AUTHORIZATION='Bearer fake_token'
            )
        
        logger.info(f"✓ Response received")
        logger.info(f"  Status Code: {response.status_code}")
        logger.info(f"  Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify ride accepted
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status, 'accepted_by_driver')
        logger.info(f"\n✓ Ride accepted with Gold grade")
        logger.info(f"  Benefit: Saved {Decimal('1000.00') - required_commission} FCFA vs Bronze")
        
        logger.info("\n✓ TEST PASSED: Gold grade allows acceptance with lower wallet balance")


@pytest.mark.django_db
class TestRideCompletionWithWallet(TestCase):
    """Test ride completion with wallet commission deduction."""
    
    def setUp(self):
        """Set up test data with detailed logging."""
        logger.info("=" * 80)
        logger.info("SETTING UP RIDE COMPLETION TESTS")
        logger.info("=" * 80)
        
        self.client_api = APIClient()
        
        # Create grade
        logger.info("Creating test grade...")
        self.bronze_grade = Grade.objects.create(
            name='Bronze',
            commission_rate=Decimal('20.00'),
            is_active=True
        )
        logger.info(f"✓ Created Bronze grade: {self.bronze_grade.commission_rate}%")
        
        # Create driver
        logger.info("\nCreating test driver...")
        self.driver = Drivers.objects.create(
            username='completion_driver',
            email='completion_driver@example.com',
            user_type='drivers',
            first_name='Completion',
            last_name='Driver',
            phone_number='+237600000020',
            password='testpass123',
            wallet_money=Decimal('10000.00'),
            is_available=False
        )
        logger.info(f"✓ Created driver: {self.driver.username}")
        logger.info(f"  Wallet balance: {self.driver.wallet_money} FCFA")
        
        # Create vehicle
        self.vehicle = Vehicle.objects.create(
            driver_id=self.driver,
            vehicle_model='Toyota Corolla',
            license_plate='COMP-001',
            validation_status='validated'
        )
        
        # Assign grade
        self.driver_grade = DriverGrade.objects.create(
            driver=self.driver,
            grade=self.bronze_grade,
            is_current=True,
            reason="Test assignment"
        )
        logger.info(f"✓ Assigned {self.bronze_grade.name} grade")
        
        # Create client
        logger.info("\nCreating test client...")
        self.client_user = Clients.objects.create(
            username='completion_client',
            email='completion_client@example.com',
            user_type='client',
            first_name='Completion',
            last_name='Client',
            phone_number='+237600000021',
            password='testpass123'
        )
        logger.info(f"✓ Created client: {self.client_user.username}")
        
        # Create in-progress ride
        logger.info("\nCreating in-progress ride...")
        self.ride = Rides.objects.create(
            client_id=self.client_user,
            driver_id=self.driver,
            final_price=Decimal('5000.00'),
            status='in_progress',
            start_location='Start Point',
            end_location='End Point'
        )
        logger.info(f"✓ Created ride: {self.ride.id}")
        logger.info(f"  Price: {self.ride.final_price} FCFA")
        logger.info(f"  Status: {self.ride.status}")
        
        logger.info("\n" + "=" * 80)
        logger.info("SETUP COMPLETE")
        logger.info("=" * 80 + "\n")
    
    def test_ride_completion_success_with_commission_deduction(self):
        """Test successful ride completion with commission deduction."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Ride Completion - Success with Commission Deduction")
        logger.info("=" * 80)
        
        initial_balance = self.driver.wallet_money
        initial_tx_count = WalletTransaction.objects.filter(driver=self.driver).count()
        
        logger.info(f"Initial State:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Grade: {self.bronze_grade.name} ({self.bronze_grade.commission_rate}%)")
        logger.info(f"  Wallet Balance: {initial_balance} FCFA")
        logger.info(f"  Ride Price: {self.ride.final_price} FCFA")
        logger.info(f"  Transaction Count: {initial_tx_count}")
        
        expected_commission = (self.ride.final_price * self.bronze_grade.commission_rate) / 100
        expected_net = self.ride.final_price - expected_commission
        expected_balance = initial_balance - expected_commission
        
        logger.info(f"\nExpected Calculations:")
        logger.info(f"  Commission: {expected_commission} FCFA")
        logger.info(f"  Net Earning: {expected_net} FCFA")
        logger.info(f"  Balance After: {expected_balance} FCFA")
        
        # Authenticate as driver
        self.client_api.force_authenticate(user=self.driver)
        
        # Mock JWT and backoffice user
        with patch('rides.views.JWT_Drivers') as mock_jwt:
            mock_jwt.filter_and_decode_token.return_value = ('fake_token', self.driver)
            with patch('payments.services.wallet_service.RetrieveBackofficeUser') as mock_backoffice:
                mock_backoffice.return_value.retrieve_backoffice_user.return_value = self.driver
                
                logger.info(f"\nCompleting ride...")
                response = self.client_api.get(
                    f'/api/rides/driver/{self.ride.id}/complete',
                    HTTP_AUTHORIZATION='Bearer fake_token'
                )
        
        logger.info(f"✓ Response received")
        logger.info(f"  Status Code: {response.status_code}")
        logger.info(f"  Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('commission_amount', response.data)
        self.assertIn('net_earning', response.data)
        self.assertIn('wallet_balance', response.data)
        
        logger.info(f"\n✓ Response Details:")
        logger.info(f"  Commission Amount: {response.data['commission_amount']} FCFA")
        logger.info(f"  Commission Rate: {response.data['commission_rate']}")
        logger.info(f"  Net Earning: {response.data['net_earning']} FCFA")
        logger.info(f"  Wallet Balance: {response.data['wallet_balance']} FCFA")
        
        # Verify ride status
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status, 'completed')
        logger.info(f"\n✓ Ride status updated: {self.ride.status}")
        
        # Verify driver available
        self.driver.refresh_from_db()
        self.assertTrue(self.driver.is_available)
        logger.info(f"✓ Driver marked available")
        
        # Verify wallet balance
        self.assertEqual(self.driver.wallet_money, expected_balance)
        logger.info(f"✓ Wallet balance updated: {self.driver.wallet_money} FCFA")
        
        # Verify wallet transaction created
        wallet_tx = WalletTransaction.objects.filter(
            driver=self.driver,
            transaction_type='commission_deduction'
        ).first()
        self.assertIsNotNone(wallet_tx)
        logger.info(f"\n✓ WalletTransaction created:")
        logger.info(f"  ID: {wallet_tx.id}")
        logger.info(f"  Type: {wallet_tx.transaction_type}")
        logger.info(f"  Amount: {wallet_tx.amount} FCFA")
        logger.info(f"  Balance Before: {wallet_tx.balance_before} FCFA")
        logger.info(f"  Balance After: {wallet_tx.balance_after} FCFA")
        logger.info(f"  Commission Rate: {wallet_tx.commission_rate}%")
        logger.info(f"  Grade: {wallet_tx.grade_name}")
        logger.info(f"  Status: {wallet_tx.status}")
        
        # Verify payment records created
        payment_count = PaymentsDrivers.objects.filter(driver_id=self.driver).count()
        self.assertEqual(payment_count, 2)  # ride_payment + wallet_pay
        logger.info(f"\n✓ Payment records created: {payment_count}")
        
        ride_payment = PaymentsDrivers.objects.filter(
            driver_id=self.driver,
            payments_type='ride_payment'
        ).first()
        wallet_payment = PaymentsDrivers.objects.filter(
            driver_id=self.driver,
            payments_type='wallet_pay'
        ).first()
        
        logger.info(f"  Ride Payment: {ride_payment.amount} FCFA ({ride_payment.payments_status})")
        logger.info(f"  Wallet Payment: {wallet_payment.amount} FCFA ({wallet_payment.payments_status})")
        
        logger.info("\n✓ TEST PASSED: Ride completed successfully with all records created")
    
    def test_ride_completion_fails_with_insufficient_wallet(self):
        """Test ride completion fails when wallet has insufficient balance."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Ride Completion - Fails with Insufficient Wallet")
        logger.info("=" * 80)
        
        # Set insufficient wallet balance
        insufficient_balance = Decimal('500.00')
        self.driver.wallet_money = insufficient_balance
        self.driver.save()
        
        logger.info(f"Initial State:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Grade: {self.bronze_grade.name} ({self.bronze_grade.commission_rate}%)")
        logger.info(f"  Wallet Balance: {self.driver.wallet_money} FCFA")
        logger.info(f"  Ride Price: {self.ride.final_price} FCFA")
        
        required_commission = (self.ride.final_price * self.bronze_grade.commission_rate) / 100
        logger.info(f"  Required Commission: {required_commission} FCFA")
        logger.info(f"  Shortfall: {required_commission - insufficient_balance} FCFA")
        
        # Authenticate as driver
        self.client_api.force_authenticate(user=self.driver)
        
        # Mock JWT
        with patch('rides.views.JWT_Drivers') as mock_jwt:
            mock_jwt.filter_and_decode_token.return_value = ('fake_token', self.driver)
            logger.info(f"\nAttempting to complete ride...")
            response = self.client_api.get(
                f'/api/rides/driver/{self.ride.id}/complete',
                HTTP_AUTHORIZATION='Bearer fake_token'
            )
        
        logger.info(f"✓ Response received")
        logger.info(f"  Status Code: {response.status_code}")
        logger.info(f"  Response: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'insufficient_wallet')
        
        logger.info(f"\n✓ Error Response:")
        logger.info(f"  Error Type: {response.data['error']}")
        logger.info(f"  Message: {response.data['Message']}")
        logger.info(f"  Details: {response.data['details']}")
        logger.info(f"  Action Required: {response.data['action_required']}")
        
        # Verify ride still in progress
        self.ride.refresh_from_db()
        self.assertEqual(self.ride.status, 'in_progress')
        logger.info(f"\n✓ Ride status unchanged: {self.ride.status}")
        
        # Verify wallet balance unchanged
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.wallet_money, insufficient_balance)
        logger.info(f"✓ Wallet balance unchanged: {self.driver.wallet_money} FCFA")
        
        # Verify no wallet transaction created
        tx_count = WalletTransaction.objects.filter(driver=self.driver).count()
        self.assertEqual(tx_count, 0)
        logger.info(f"✓ No transactions created (count: {tx_count})")
        
        # Verify driver still unavailable
        self.assertFalse(self.driver.is_available)
        logger.info(f"✓ Driver still unavailable (can retry after recharge)")
        
        logger.info("\n✓ TEST PASSED: Insufficient wallet properly prevents completion")
    
    def test_ride_completion_atomic_rollback_on_error(self):
        """Test that ride completion rolls back completely on error."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Ride Completion - Atomic Rollback on Error")
        logger.info("=" * 80)
        
        initial_balance = self.driver.wallet_money
        initial_status = self.ride.status
        
        logger.info(f"Initial State:")
        logger.info(f"  Wallet Balance: {initial_balance} FCFA")
        logger.info(f"  Ride Status: {initial_status}")
        logger.info(f"  Driver Available: {self.driver.is_available}")
        
        # Set insufficient balance to trigger error
        self.driver.wallet_money = Decimal('100.00')
        self.driver.save()
        
        logger.info(f"\nSet insufficient balance: {self.driver.wallet_money} FCFA")
        logger.info(f"Required: {(self.ride.final_price * Decimal('20.00')) / 100} FCFA")
        
        # Authenticate as driver
        self.client_api.force_authenticate(user=self.driver)
        
        # Mock JWT
        with patch('rides.views.JWT_Drivers') as mock_jwt:
            mock_jwt.filter_and_decode_token.return_value = ('fake_token', self.driver)
            
            logger.info(f"\nAttempting completion (should fail)...")
            response = self.client_api.get(
                f'/api/rides/driver/{self.ride.id}/complete',
                HTTP_AUTHORIZATION='Bearer fake_token'
            )
        
        logger.info(f"✓ Error response received: {response.status_code}")
        
        # Verify everything rolled back
        self.ride.refresh_from_db()
        self.driver.refresh_from_db()
        
        logger.info(f"\nVerifying rollback:")
        logger.info(f"  Ride Status: {self.ride.status} (should be {initial_status})")
        logger.info(f"  Wallet Balance: {self.driver.wallet_money} FCFA")
        logger.info(f"  Driver Available: {self.driver.is_available}")
        
        self.assertEqual(self.ride.status, initial_status)
        self.assertEqual(self.driver.wallet_money, Decimal('100.00'))
        self.assertFalse(self.driver.is_available)
        
        # Verify no transactions created
        tx_count = WalletTransaction.objects.filter(driver=self.driver).count()
        payment_count = PaymentsDrivers.objects.filter(driver_id=self.driver).count()
        
        logger.info(f"  Wallet Transactions: {tx_count}")
        logger.info(f"  Payment Records: {payment_count}")
        
        self.assertEqual(tx_count, 0)
        self.assertEqual(payment_count, 0)
        
        logger.info("\n✓ TEST PASSED: Complete atomic rollback on error")
