"""
Quick test script to verify wallet recharge functionality.
Run this script to test the wallet update flow.
"""
import os
import django
import sys
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from drivers.models import Drivers, Grade, DriverGrade
from payments.models import PaymentsDrivers, WalletTransaction
from payments.payment import PaymentProcess
from payments.services.wallet_service import WalletService
from unittest.mock import patch

def test_wallet_deposit():
    """Test wallet deposit processing."""
    print("=" * 80)
    print("TESTING WALLET RECHARGE FLOW")
    print("=" * 80)
    
    # Find or create a test driver
    try:
        driver = Drivers.objects.filter(phone_number='+237600000099').first()
        if not driver:
            print("\n❌ No test driver found. Creating one...")
            driver = Drivers.objects.create(
                username='test_wallet_driver',
                email='test_wallet@example.com',
                user_type='drivers',
                first_name='Test',
                last_name='Driver',
                phone_number='+237600000099',
                password='testpass123',
                wallet_money=Decimal('1000.00'),
                is_available=True
            )
            print(f"✓ Created test driver: {driver.id}")
        else:
            print(f"\n✓ Using existing driver: {driver.id}")
        
        initial_balance = driver.wallet_money
        print(f"  Initial wallet balance: {initial_balance} FCFA")
        
        # Create a deposit transaction
        deposit_amount = Decimal('5000.00')
        print(f"\n📝 Creating deposit transaction for {deposit_amount} FCFA...")
        
        payment = PaymentsDrivers.objects.create(
            driver_id=driver,
            amount=float(deposit_amount),
            payments_method='orange_money',
            payments_type='wallet_pay',
            payments_status='in_pending'
        )
        print(f"✓ Payment created: {payment.id}")
        print(f"  Status: {payment.payments_status}")
        
        # Process the payment as SUCCESS
        print(f"\n⚙️  Processing payment as SUCCESS...")
        payment_processor = PaymentProcess()
        
        with patch('payments.payment.RetrieveBackofficeUser') as mock_backoffice:
            mock_backoffice.return_value.retrieve_backoffice_user.return_value = driver
            payment_processor.launch_process('SUCCESS', str(payment.id))
        
        # Verify wallet balance updated
        driver.refresh_from_db()
        expected_balance = initial_balance + deposit_amount
        
        print(f"\n📊 RESULTS:")
        print(f"  Initial Balance:  {initial_balance} FCFA")
        print(f"  Deposit Amount:   {deposit_amount} FCFA")
        print(f"  Expected Balance: {expected_balance} FCFA")
        print(f"  Actual Balance:   {driver.wallet_money} FCFA")
        
        if driver.wallet_money == expected_balance:
            print(f"\n✅ SUCCESS: Wallet balance updated correctly!")
        else:
            print(f"\n❌ FAILURE: Wallet balance mismatch!")
            print(f"   Difference: {driver.wallet_money - expected_balance} FCFA")
            return False
        
        # Verify payment status
        payment.refresh_from_db()
        print(f"\n💳 Payment Status: {payment.payments_status}")
        if payment.payments_status == 'completed':
            print(f"✅ Payment marked as completed")
        else:
            print(f"❌ Payment status incorrect: {payment.payments_status}")
            return False
        
        # Verify wallet transaction created
        wallet_tx = WalletTransaction.objects.filter(
            driver=driver,
            transaction_type='deposit',
            payment=payment
        ).first()
        
        if wallet_tx:
            print(f"\n📝 WalletTransaction Record:")
            print(f"  ID: {wallet_tx.id}")
            print(f"  Type: {wallet_tx.transaction_type}")
            print(f"  Amount: {wallet_tx.amount} FCFA")
            print(f"  Balance Before: {wallet_tx.balance_before} FCFA")
            print(f"  Balance After: {wallet_tx.balance_after} FCFA")
            print(f"  Status: {wallet_tx.status}")
            print(f"✅ Transaction record created correctly")
        else:
            print(f"\n❌ No WalletTransaction record found!")
            return False
        
        # Test idempotency - process same payment again
        print(f"\n🔄 Testing idempotency (processing same payment again)...")
        balance_before_retry = driver.wallet_money
        
        with patch('payments.payment.RetrieveBackofficeUser') as mock_backoffice:
            mock_backoffice.return_value.retrieve_backoffice_user.return_value = driver
            payment_processor.launch_process('SUCCESS', str(payment.id))
        
        driver.refresh_from_db()
        if driver.wallet_money == balance_before_retry:
            print(f"✅ Idempotency check passed - balance unchanged: {driver.wallet_money} FCFA")
        else:
            print(f"❌ Idempotency check failed - balance changed!")
            return False
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - WALLET RECHARGE WORKING CORRECTLY!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_wallet_deposit()
    sys.exit(0 if success else 1)
