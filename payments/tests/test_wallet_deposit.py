"""
Tests for wallet deposit flow with detailed logging.
Tests cover successful deposits, failed deposits, and transaction record creation.
"""
import pytest
import logging
from decimal import Decimal
from django.test import TestCase
from unittest.mock import patch, MagicMock

from drivers.models import Drivers, Grade, DriverGrade
from payments.models import WalletTransaction, PaymentsDrivers
from payments.payment import PaymentProcess
from payments.services.wallet_service import WalletService

# Configure logging for tests
logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestWalletDeposit(TestCase):
    """Test wallet deposit processing with transaction tracking."""
    
    def setUp(self):
        """Set up test data with detailed logging."""
        logger.info("=" * 80)
        logger.info("SETTING UP WALLET DEPOSIT TESTS")
        logger.info("=" * 80)
        
        # Create grade
        logger.info("Creating test grade...")
        self.grade = Grade.objects.create(
            name='Bronze',
            commission_rate=Decimal('20.00'),
            is_active=True
        )
        logger.info(f"✓ Created Bronze grade")
        
        # Create driver
        logger.info("\nCreating test driver...")
        self.driver = Drivers.objects.create(
            username='deposit_driver',
            email='deposit_driver@example.com',
            user_type='drivers',
            first_name='Deposit',
            last_name='Driver',
            phone_number='+237600000030',
            password='testpass123',
            wallet_money=Decimal('1000.00'),
            is_available=True
        )
        logger.info(f"✓ Created driver: {self.driver.username}")
        logger.info(f"  Initial wallet balance: {self.driver.wallet_money} FCFA")
        
        # Assign grade
        self.driver_grade = DriverGrade.objects.create(
            driver=self.driver,
            grade=self.grade,
            is_current=True,
            reason="Test assignment"
        )
        logger.info(f"✓ Assigned {self.grade.name} grade")
        
        logger.info("\n" + "=" * 80)
        logger.info("SETUP COMPLETE")
        logger.info("=" * 80 + "\n")
    
    def test_successful_deposit_via_orange_money(self):
        """Test successful wallet deposit via Orange Money."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Successful Deposit - Orange Money")
        logger.info("=" * 80)
        
        deposit_amount = Decimal('5000.00')
        initial_balance = self.driver.wallet_money
        
        logger.info(f"Deposit Details:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Initial Balance: {initial_balance} FCFA")
        logger.info(f"  Deposit Amount: {deposit_amount} FCFA")
        logger.info(f"  Payment Method: Orange Money")
        logger.info(f"  Expected Balance: {initial_balance + deposit_amount} FCFA")
        
        # Create pending payment
        logger.info(f"\nCreating pending payment transaction...")
        payment = PaymentsDrivers.objects.create(
            driver_id=self.driver,
            amount=float(deposit_amount),
            payments_method='orange_money',
            payments_type='wallet_pay',
            payments_status='in_pending'
        )
        logger.info(f"✓ Payment created:")
        logger.info(f"  ID: {payment.id}")
        logger.info(f"  Amount: {payment.amount} FCFA")
        logger.info(f"  Method: {payment.payments_method}")
        logger.info(f"  Status: {payment.payments_status}")
        
        # Process successful payment
        logger.info(f"\nProcessing payment as SUCCESS...")
        payment_processor = PaymentProcess()
        
        with patch('payments.payment.RetrieveBackofficeUser') as mock_backoffice:
            mock_backoffice.return_value.retrieve_backoffice_user.return_value = self.driver
            payment_processor.launch_process('SUCCESS', str(payment.id))
        
        logger.info(f"✓ Payment processed")
        
        # Verify wallet balance updated
        self.driver.refresh_from_db()
        expected_balance = initial_balance + deposit_amount
        self.assertEqual(self.driver.wallet_money, expected_balance)
        logger.info(f"\n✓ Wallet balance updated:")
        logger.info(f"  Before: {initial_balance} FCFA")
        logger.info(f"  After: {self.driver.wallet_money} FCFA")
        logger.info(f"  Increase: +{deposit_amount} FCFA")
        
        # Verify payment status updated
        payment.refresh_from_db()
        self.assertEqual(payment.payments_status, 'completed')
        logger.info(f"\n✓ Payment status updated: {payment.payments_status}")
        
        # Verify wallet transaction created
        wallet_tx = WalletTransaction.objects.filter(
            driver=self.driver,
            transaction_type='deposit'
        ).first()
        self.assertIsNotNone(wallet_tx)
        logger.info(f"\n✓ WalletTransaction created:")
        logger.info(f"  ID: {wallet_tx.id}")
        logger.info(f"  Type: {wallet_tx.transaction_type}")
        logger.info(f"  Amount: {wallet_tx.amount} FCFA")
        logger.info(f"  Balance Before: {wallet_tx.balance_before} FCFA")
        logger.info(f"  Balance After: {wallet_tx.balance_after} FCFA")
        logger.info(f"  Description: {wallet_tx.description}")
        logger.info(f"  Status: {wallet_tx.status}")
        
        self.assertEqual(wallet_tx.amount, deposit_amount)
        self.assertEqual(wallet_tx.balance_before, initial_balance)
        self.assertEqual(wallet_tx.balance_after, expected_balance)
        self.assertEqual(wallet_tx.status, 'completed')
        
        logger.info("\n✓ TEST PASSED: Deposit processed successfully")
    
    def test_successful_deposit_via_mtn_money(self):
        """Test successful wallet deposit via MTN Money."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Successful Deposit - MTN Money")
        logger.info("=" * 80)
        
        deposit_amount = Decimal('3000.00')
        initial_balance = self.driver.wallet_money
        
        logger.info(f"Deposit Details:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Initial Balance: {initial_balance} FCFA")
        logger.info(f"  Deposit Amount: {deposit_amount} FCFA")
        logger.info(f"  Payment Method: MTN Money")
        
        # Create and process payment
        logger.info(f"\nCreating and processing payment...")
        payment = PaymentsDrivers.objects.create(
            driver_id=self.driver,
            amount=float(deposit_amount),
            payments_method='mtn_money',
            payments_type='wallet_pay',
            payments_status='in_pending'
        )
        
        payment_processor = PaymentProcess()
        with patch('payments.payment.RetrieveBackofficeUser') as mock_backoffice:
            mock_backoffice.return_value.retrieve_backoffice_user.return_value = self.driver
            payment_processor.launch_process('SUCCESS', str(payment.id))
        
        logger.info(f"✓ Payment processed")
        
        # Verify results
        self.driver.refresh_from_db()
        expected_balance = initial_balance + deposit_amount
        self.assertEqual(self.driver.wallet_money, expected_balance)
        
        logger.info(f"\n✓ Wallet updated: {initial_balance} → {self.driver.wallet_money} FCFA")
        logger.info(f"✓ Payment method: {payment.payments_method}")
        
        logger.info("\n✓ TEST PASSED: MTN Money deposit successful")
    
    def test_failed_deposit_payment(self):
        """Test failed deposit payment handling."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Failed Deposit Payment")
        logger.info("=" * 80)
        
        deposit_amount = Decimal('2000.00')
        initial_balance = self.driver.wallet_money
        
        logger.info(f"Deposit Details:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Initial Balance: {initial_balance} FCFA")
        logger.info(f"  Attempted Deposit: {deposit_amount} FCFA")
        logger.info(f"  Expected Outcome: FAILED")
        
        # Create pending payment
        logger.info(f"\nCreating pending payment...")
        payment = PaymentsDrivers.objects.create(
            driver_id=self.driver,
            amount=float(deposit_amount),
            payments_method='orange_money',
            payments_type='wallet_pay',
            payments_status='in_pending'
        )
        logger.info(f"✓ Payment created: {payment.id}")
        
        # Process as failed
        logger.info(f"\nProcessing payment as FAILED...")
        payment_processor = PaymentProcess()
        
        with patch('payments.payment.RetrieveBackofficeUser') as mock_backoffice:
            mock_backoffice.return_value.retrieve_backoffice_user.return_value = self.driver
            payment_processor.launch_process('FAILED', str(payment.id))
        
        logger.info(f"✓ Payment processed as failed")
        
        # Verify wallet balance unchanged
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.wallet_money, initial_balance)
        logger.info(f"\n✓ Wallet balance unchanged: {self.driver.wallet_money} FCFA")
        
        # Verify payment status
        payment.refresh_from_db()
        self.assertEqual(payment.payments_status, 'failed')
        logger.info(f"✓ Payment status: {payment.payments_status}")
        
        # Verify no wallet transaction created
        wallet_tx_count = WalletTransaction.objects.filter(
            driver=self.driver,
            transaction_type='deposit'
        ).count()
        self.assertEqual(wallet_tx_count, 0)
        logger.info(f"✓ No WalletTransaction created (count: {wallet_tx_count})")
        
        logger.info("\n✓ TEST PASSED: Failed payment handled correctly")
    
    def test_pending_deposit_payment(self):
        """Test pending deposit payment status."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Pending Deposit Payment")
        logger.info("=" * 80)
        
        deposit_amount = Decimal('1500.00')
        initial_balance = self.driver.wallet_money
        
        logger.info(f"Deposit Details:")
        logger.info(f"  Driver: {self.driver.username}")
        logger.info(f"  Initial Balance: {initial_balance} FCFA")
        logger.info(f"  Deposit Amount: {deposit_amount} FCFA")
        logger.info(f"  Status: PENDING")
        
        # Create pending payment
        payment = PaymentsDrivers.objects.create(
            driver_id=self.driver,
            amount=float(deposit_amount),
            payments_method='orange_money',
            payments_type='wallet_pay',
            payments_status='in_pending'
        )
        logger.info(f"\n✓ Payment created: {payment.id}")
        
        # Process as pending
        logger.info(f"\nProcessing payment as PENDING...")
        payment_processor = PaymentProcess()
        payment_processor.launch_process('PENDING', str(payment.id))
        logger.info(f"✓ Payment remains pending")
        
        # Verify wallet balance unchanged
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.wallet_money, initial_balance)
        logger.info(f"\n✓ Wallet balance unchanged: {self.driver.wallet_money} FCFA")
        
        # Verify payment status unchanged
        payment.refresh_from_db()
        self.assertEqual(payment.payments_status, 'in_pending')
        logger.info(f"✓ Payment status: {payment.payments_status}")
        
        # Verify no wallet transaction created
        wallet_tx_count = WalletTransaction.objects.filter(driver=self.driver).count()
        self.assertEqual(wallet_tx_count, 0)
        logger.info(f"✓ No WalletTransaction created (count: {wallet_tx_count})")
        
        logger.info("\n✓ TEST PASSED: Pending payment handled correctly")
    
    def test_multiple_deposits_transaction_history(self):
        """Test multiple deposits create proper transaction history."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Multiple Deposits - Transaction History")
        logger.info("=" * 80)
        
        initial_balance = self.driver.wallet_money
        logger.info(f"Initial Balance: {initial_balance} FCFA")
        
        deposits = [
            (Decimal('1000.00'), 'orange_money'),
            (Decimal('2000.00'), 'mtn_money'),
            (Decimal('1500.00'), 'orange_money'),
        ]
        
        logger.info(f"\nProcessing {len(deposits)} deposits...")
        
        expected_balance = initial_balance
        for i, (amount, method) in enumerate(deposits, 1):
            logger.info(f"\n--- Deposit {i} ---")
            logger.info(f"  Amount: {amount} FCFA")
            logger.info(f"  Method: {method}")
            
            payment = PaymentsDrivers.objects.create(
                driver_id=self.driver,
                amount=float(amount),
                payments_method=method,
                payments_type='wallet_pay',
                payments_status='in_pending'
            )
            
            payment_processor = PaymentProcess()
            with patch('payments.payment.RetrieveBackofficeUser') as mock_backoffice:
                mock_backoffice.return_value.retrieve_backoffice_user.return_value = self.driver
                payment_processor.launch_process('SUCCESS', str(payment.id))
            
            expected_balance += amount
            logger.info(f"  ✓ Processed - New balance: {expected_balance} FCFA")
        
        # Verify final balance
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.wallet_money, expected_balance)
        logger.info(f"\n✓ Final wallet balance: {self.driver.wallet_money} FCFA")
        logger.info(f"  Total deposited: {expected_balance - initial_balance} FCFA")
        
        # Verify transaction history
        transactions = WalletTransaction.objects.filter(
            driver=self.driver,
            transaction_type='deposit'
        ).order_by('created_at')
        
        self.assertEqual(transactions.count(), len(deposits))
        logger.info(f"\n✓ Transaction history ({transactions.count()} records):")
        
        for i, tx in enumerate(transactions, 1):
            logger.info(f"\n  Transaction {i}:")
            logger.info(f"    Amount: {tx.amount} FCFA")
            logger.info(f"    Balance: {tx.balance_before} → {tx.balance_after} FCFA")
            logger.info(f"    Description: {tx.description}")
            logger.info(f"    Status: {tx.status}")
            logger.info(f"    Created: {tx.created_at}")
        
        logger.info("\n✓ TEST PASSED: Multiple deposits tracked correctly")
    
    def test_idempotent_deposit_processing(self):
        """Test that processing same deposit twice doesn't double-credit."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST: Idempotent Deposit Processing")
        logger.info("=" * 80)
        
        deposit_amount = Decimal('5000.00')
        initial_balance = self.driver.wallet_money
        
        logger.info(f"Initial Balance: {initial_balance} FCFA")
        logger.info(f"Deposit Amount: {deposit_amount} FCFA")
        
        # Create and process payment
        logger.info(f"\nProcessing deposit (first time)...")
        payment = PaymentsDrivers.objects.create(
            driver_id=self.driver,
            amount=float(deposit_amount),
            payments_method='orange_money',
            payments_type='wallet_pay',
            payments_status='in_pending'
        )
        
        payment_processor = PaymentProcess()
        with patch('payments.payment.RetrieveBackofficeUser') as mock_backoffice:
            mock_backoffice.return_value.retrieve_backoffice_user.return_value = self.driver
            payment_processor.launch_process('SUCCESS', str(payment.id))
        
        self.driver.refresh_from_db()
        balance_after_first = self.driver.wallet_money
        logger.info(f"✓ First processing: {initial_balance} → {balance_after_first} FCFA")
        
        # Try to process same payment again
        logger.info(f"\nAttempting to process same deposit again...")
        with patch('payments.payment.RetrieveBackofficeUser') as mock_backoffice:
            mock_backoffice.return_value.retrieve_backoffice_user.return_value = self.driver
            payment_processor.launch_process('SUCCESS', str(payment.id))
        
        self.driver.refresh_from_db()
        balance_after_second = self.driver.wallet_money
        logger.info(f"✓ Second processing: {balance_after_second} FCFA")
        
        # Verify balance didn't change on second processing
        self.assertEqual(balance_after_first, balance_after_second)
        logger.info(f"\n✓ Balance unchanged on duplicate processing")
        logger.info(f"  Expected: {balance_after_first} FCFA")
        logger.info(f"  Actual: {balance_after_second} FCFA")
        
        # Verify only one transaction created
        tx_count = WalletTransaction.objects.filter(
            driver=self.driver,
            transaction_type='deposit'
        ).count()
        self.assertEqual(tx_count, 1)
        logger.info(f"✓ Only one transaction created (count: {tx_count})")
        
        logger.info("\n✓ TEST PASSED: Idempotent processing prevents double-credit")
