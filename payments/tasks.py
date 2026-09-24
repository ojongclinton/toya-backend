"""
Celery tasks for payment processing.
"""
import logging
import time
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def verify_payment_status_task(self, transaction_id):
    """
    Background task to automatically verify payment status.
    Polls S3 Mobile Pay API every 20 seconds for up to 130 seconds (6 attempts).
    Updates wallet automatically when payment succeeds.
    
    Args:
        transaction_id: UUID of the PaymentsDrivers transaction
        
    Returns:
        dict: Final status of the payment
    """
    from payments.payments.smobilepay.cashout import S3CashOutManager
    from payments.models import PaymentsDrivers
    
    try:
        logger.info(f"Starting background verification for transaction {transaction_id}")
        
        # Verify transaction exists
        try:
            transaction = PaymentsDrivers.objects.get(id=transaction_id)
        except PaymentsDrivers.DoesNotExist:
            logger.error(f"Transaction {transaction_id} not found")
            return {'status': 'ERROR', 'message': 'Transaction not found'}
        
        s3_manager = S3CashOutManager()
        max_attempts = 6  # 6 attempts × 20 seconds = 120 seconds
        interval = 20  # seconds
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Checking payment status (attempt {attempt}/{max_attempts}) for transaction {transaction_id}")
            
            # Check transaction status
            status_response = s3_manager.checkTransactionStatus(transaction_id)
            
            if not status_response:
                logger.warning(f"No response from status check for transaction {transaction_id}")
                time.sleep(interval)
                continue
            
            status = status_response.get('status', 'UNKNOWN')
            logger.info(f"Transaction {transaction_id} status: {status}")
            
            # If payment succeeded or failed, stop polling
            if status == 'SUCCESS':
                logger.info(f"Payment successful for transaction {transaction_id}. Wallet updated by checkTransactionStatus.")
                return {
                    'status': 'SUCCESS',
                    'transaction_id': transaction_id,
                    'attempts': attempt,
                    'details': status_response
                }
            
            elif status in ['FAILED', 'ERRORED']:
                logger.warning(f"Payment failed for transaction {transaction_id}: {status}")
                return {
                    'status': status,
                    'transaction_id': transaction_id,
                    'attempts': attempt,
                    'details': status_response
                }
            
            # Status is PENDING, continue polling
            if attempt < max_attempts:
                logger.info(f"Payment still pending for transaction {transaction_id}. Waiting {interval}s before next check...")
                time.sleep(interval)
        
        # Max attempts reached, payment still pending
        logger.warning(f"Payment verification timeout for transaction {transaction_id} after {max_attempts} attempts")
        return {
            'status': 'TIMEOUT',
            'transaction_id': transaction_id,
            'attempts': max_attempts,
            'message': 'Payment verification timeout. Status still pending after 120 seconds.'
        }
        
    except Exception as e:
        logger.error(f"Error in payment verification task for transaction {transaction_id}: {str(e)}", exc_info=True)
        return {
            'status': 'ERROR',
            'transaction_id': transaction_id,
            'error': str(e)
        }
