"""
Wallet Service - Centralized wallet management
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from drivers.models import Drivers, DriverGrade
from payments.models import WalletTransaction, PaymentsDrivers
from notifications.models import Notifications
from notifications.custums import RetrieveBackofficeUser
from core.utils.translations import get_message
from core.utils.language import get_user_language

logger = logging.getLogger(__name__)


class WalletService:
    """
    Service for managing driver wallet operations.
    All wallet modifications should go through this service.
    """
    
    @staticmethod
    def get_driver_commission_rate(driver):
        """
        Get the current commission rate for a driver based on their grade.
        
        Args:
            driver: Drivers instance
            
        Returns:
            Decimal: Commission rate percentage
        """
        driver_grade = DriverGrade.objects.filter(
            driver=driver, 
            is_current=True
        ).select_related('grade').first()
        
        if driver_grade:
            return driver_grade.grade.commission_rate
        return Decimal('15.00')  # Default fallback
    
    @staticmethod
    def calculate_commission(ride_price, commission_rate):
        """
        Calculate commission amount for a ride.
        
        Args:
            ride_price: Decimal or float
            commission_rate: Decimal percentage
            
        Returns:
            tuple: (commission_amount, net_earning)
        """
        ride_price = Decimal(str(ride_price))
        commission_amount = (ride_price * commission_rate) / 100
        net_earning = ride_price - commission_amount
        
        return commission_amount, net_earning
    
    @staticmethod
    @transaction.atomic
    def process_ride_commission(ride, driver):
        """
        Process commission deduction after ride completion.
        Creates wallet transactions and updates balance.
        
        Args:
            ride: Rides instance
            driver: Drivers instance
            
        Returns:
            dict: Transaction details
            
        Raises:
            ValueError: If insufficient wallet balance
        """
        # Get driver's grade and commission rate
        driver_grade = DriverGrade.objects.filter(
            driver=driver, 
            is_current=True
        ).select_related('grade').first()
        
        commission_rate = driver_grade.grade.commission_rate if driver_grade else Decimal('20.00')
        grade_name = driver_grade.grade.name if driver_grade else 'Standard'
        
        # Calculate amounts
        gross_amount = Decimal(str(ride.final_price))
        commission_amount, net_earning = WalletService.calculate_commission(
            gross_amount, 
            commission_rate
        )
        
        balance_before = driver.wallet_money
        
        # Verify sufficient balance
        if balance_before < commission_amount:
            raise ValueError(
                f"Solde wallet insuffisant. Requis: {commission_amount} FCFA, "
                f"Disponible: {balance_before} FCFA"
            )
        
        # Deduct commission from wallet
        balance_after = balance_before - commission_amount
        
        # Create commission deduction transaction
        commission_tx = WalletTransaction.objects.create(
            driver=driver,
            transaction_type='commission_deduction',
            amount=commission_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            ride=ride,
            commission_rate=commission_rate,
            grade_name=grade_name,
            description=f"Commission ({commission_rate}%) pour course {ride.id}",
            status='completed'
        )
        
        # Update driver wallet balance
        driver.wallet_money = balance_after
        driver.save()
        
        # Create payment records (for backward compatibility)
        # Net earning record
        PaymentsDrivers.objects.create(
            driver_id=driver,
            amount=float(net_earning),
            payments_type='ride_payment',
            payments_status='completed'
        )
        
        # Commission record
        PaymentsDrivers.objects.create(
            driver_id=driver,
            amount=float(commission_amount),
            payments_type='wallet_pay',
            payments_status='completed'
        )
        
        # Send notification
        try:
            backoffice_user = RetrieveBackofficeUser().retrieve_backoffice_user(driver.id)
            Notifications.objects.create(
                sender=backoffice_user,
                recipient=driver,
                notification_type='withdraw_wallet',
                message=get_message("commission_deducted", get_user_language, amount=commission_amount, rate=commission_rate),
                event_id=commission_tx.id
            )
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
        
        logger.info(
            f"Commission processed: Driver {driver.id}, "
            f"Ride {ride.id}, Amount {commission_amount} FCFA"
        )
        
        return {
            'commission_amount': commission_amount,
            'net_earning': net_earning,
            'commission_rate': commission_rate,
            'balance_after': balance_after,
            'transaction_id': str(commission_tx.id)
        }
    
    @staticmethod
    @transaction.atomic
    def process_deposit_success(transaction_id):
        """
        Process successful wallet deposit from S3 Mobile Pay.
        
        Args:
            transaction_id: PaymentsDrivers transaction ID
        """
        try:
            payment = PaymentsDrivers.objects.select_for_update().get(id=transaction_id)
        except PaymentsDrivers.DoesNotExist:
            logger.error(f"Payment transaction {transaction_id} not found")
            raise
        
        # Double-check if already processed
        if payment.payments_status == 'completed':
            logger.warning(f"Payment {transaction_id} already completed, skipping")
            return
        
        driver = payment.driver_id
        amount = Decimal(str(payment.amount))
        
        logger.info(f"Processing deposit for driver {driver.id}: {amount} FCFA")
        
        # Get current balance with lock to prevent race conditions
        driver.refresh_from_db()
        balance_before = driver.wallet_money
        balance_after = balance_before + amount
        
        logger.info(f"Wallet update: {balance_before} FCFA → {balance_after} FCFA")
        
        # Create deposit transaction record
        wallet_tx = WalletTransaction.objects.create(
            driver=driver,
            transaction_type='deposit',
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            payment=payment,
            description=f"Dépôt wallet via {payment.payments_method}",
            status='completed'
        )
        logger.info(f"Created WalletTransaction {wallet_tx.id}")
        
        # Update driver balance
        driver.wallet_money = balance_after
        driver.save(update_fields=['wallet_money'])
        logger.info(f"Updated driver {driver.id} wallet_money to {driver.wallet_money} FCFA")
        
        # Update payment status
        payment.payments_status = 'completed'
        payment.save(update_fields=['payments_status'])
        logger.info(f"Updated payment {payment.id} status to completed")
        
        # Send WebSocket notification for real-time wallet update
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'ride_updates_{driver.id}',
                {
                    'type': 'wallet_update',
                    'message': {
                        'event_type': 'wallet_deposit',
                        'transaction_id': str(payment.id),
                        'amount': float(amount),
                        'balance_before': float(balance_before),
                        'balance_after': float(balance_after),
                        'payment_method': payment.payments_method,
                        'timestamp': wallet_tx.created_at.isoformat()
                    }
                }
            )
            logger.info(f"WebSocket notification sent for wallet deposit to driver {driver.id}")
        except Exception as e:
            logger.warning(f"Failed to send WebSocket notification: {e}")
        
        logger.info(f"Deposit processed successfully: Driver {driver.id}, Amount {amount} FCFA, New Balance {balance_after} FCFA")
    
    @staticmethod
    def get_balance(driver):
        """Get current wallet balance for a driver."""
        return driver.wallet_money
    
    @staticmethod
    def get_transaction_history(driver, limit=50):
        """
        Get wallet transaction history for a driver.
        
        Args:
            driver: Drivers instance
            limit: Number of transactions to return
            
        Returns:
            QuerySet: WalletTransaction objects
        """
        return WalletTransaction.objects.filter(
            driver=driver
        ).select_related('ride', 'payment')[:limit]
