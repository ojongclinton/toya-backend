from drivers.models import Drivers
from notifications.custums import RetrieveBackofficeUser
from notifications.models import Notifications
from .models import PaymentsDrivers
from payments.services.wallet_service import WalletService
import logging
from core.utils.translations import get_message
from core.utils.language import get_user_language

logger = logging.getLogger(__name__)



class PaymentProcess:
    def __init__(self):
        pass

    def launch_process(self, status_payment, transaction_id):

        try:
            transaction = PaymentsDrivers.objects.get(id=transaction_id)
        except PaymentsDrivers.DoesNotExist:
            logger.error(f"Transaction not found: {transaction_id}")
            print("Transaction not found.")
            return
        
        # Check if already processed to prevent duplicate processing
        if transaction.payments_status == 'completed':
            logger.info(f"Transaction {transaction_id} already completed, skipping")
            return
        
        driver = Drivers.objects.get(id=str(transaction.driver_id.id))
        transaction_amount = transaction.amount

        if status_payment == 'SUCCESS':
            try:
                # Use WalletService to process deposit
                # This will update wallet balance, create transaction record, and update payment status
                WalletService.process_deposit_success(transaction_id)
                logger.info(f"Deposit successful: {transaction_id}")
                
                # Refresh driver to get updated wallet balance
                driver.refresh_from_db()
                
                # Send success notification
                backoffice_user = RetrieveBackofficeUser().retrieve_backoffice_user(driver.id)
                notification = Notifications.objects.create(
                    sender=backoffice_user,
                    recipient=driver,
                    notification_type='recharge_wallet',
                    message=get_message("recharge_wallet", get_user_language, amount=transaction_amount, balance=driver.wallet_money),
                    event_id=driver.id,
                )
                notification.save()
                logger.info(f"Payment recorded successfully. New wallet balance: {driver.wallet_money} FCFA")
                print(f"Payment recorded successfully. Driver wallet updated to {driver.wallet_money} FCFA")
                
            except Exception as e:
                logger.error(f"Failed to process deposit {transaction_id}: {e}")
                print(f"Error processing deposit: {e}")
                # Mark transaction as failed if processing error occurs
                transaction.payments_status = 'failed'
                transaction.save()

        elif status_payment == 'FAILED':
            if transaction.payments_status != 'failed': 
                transaction.payments_status = 'failed'
                transaction.save()
                print("Payment failed, recorded in system.")

                backoffice_user = RetrieveBackofficeUser().retrieve_backoffice_user(driver.id)

                notification = Notifications.objects.create(
                    sender=backoffice_user,
                    recipient=driver,
                    notification_type='payment_failed',
                    message=get_message("payment_failed", get_user_language),
                    event_id=driver.id,
                )
                notification.save()

        elif status_payment == 'PENDING':
            print(f"payment status: {status_payment}")

        else:
            print(f"Unhandled payment status: {status_payment}")
