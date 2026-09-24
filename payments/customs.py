
from clients.models import Clients 
from drivers.models import Drivers
from payments.payments.smobilepay.cashout import S3CashOutManager
from .models import PaymentsDrivers
from notifications.models import Notifications
from notifications.custums import RetrieveBackofficeUser
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

    

    
class WalletPayment:
    def __init__(self) -> None:
        pass
    
    
    def make_deposit_to_his_wallet_account(payment_method , amount  , users , phone_number): 
        
        s3CashOutManager = S3CashOutManager()

        serviceId , payItemId = s3CashOutManager.get_service_information(payment_method)

        if serviceId == None and  payItemId == None  : 
            raise Exception("Select an Available Payment method")
        

        quoteId , response = s3CashOutManager.initiateTransaction(payItemId ,amount )
        if quoteId == None or response == None  : 
            raise Exception("Failed to initiate transaction. Please check API credentials and try again.")
        
        driver_instance = Drivers.objects.get(id = users.id)
        transaction = PaymentsDrivers.objects.create( 
            driver_id= driver_instance, 
            amount = amount, 
            payments_method= payment_method, 
            payments_type= 'wallet_pay', 
        )
        transaction.save()

        transactionId = str(transaction.id)
        
        ptn, response_collect = s3CashOutManager.processTransactionWithCollectStd(quoteId, phone_number, transactionId)
        
        # If API call times out or returns None, transaction is still pending
        # The WebSocket consumer will poll for status updates
        if ptn == None and response_collect == None:
            logger.warning(f"Payment collection API returned None - transaction {transactionId} remains pending")
            # Don't mark as failed - it's still pending
            # Return transaction ID so user can track via WebSocket
            return transactionId
        
        # Store PTN for tracking
        logger.info(f"Payment collection successful. Transaction ID: {transactionId}, PTN: {ptn}")
        
        return transactionId





    
    def retrieve_a_wallet_driver_amount(final_rides , driver_id, percentage=None): 
        """Appliquer le transfert du wallet du driver to toya"""
        
        try:
            drivers = Drivers.objects.get(id = driver_id)
            
            # Get commission rate from grade if not provided
            if percentage is None:
                driver_grade = DriverGrade.objects.filter(
                    driver=drivers, 
                    is_current=True
                ).select_related('grade').first()
                percentage = float(driver_grade.grade.commission_rate) if driver_grade else 15.0
            
            amout_to_send_to_app = Decimal(final_rides) * Decimal(percentage)/ 100
            
            
            if drivers.wallet_money   >   amout_to_send_to_app  : 
                payments = PaymentsDrivers.objects.create( 
                                                    driver_id  = drivers , 
                                                    amount     = (Decimal(final_rides)  - amout_to_send_to_app )  , 
                                                    payments_type = 'ride_payment', 
                                                    payments_status = 'completed'
                                                    
                                                    )
                payments.save()
                
                # start le transert 
                drivers.wallet_money -= amout_to_send_to_app 
                drivers.save()
            
                payments = PaymentsDrivers.objects.create( 
                                                    driver_id  = drivers , 
                                                    amount     = amout_to_send_to_app , 
                                                    payments_type = 'wallet_pay', 
                                                    payments_status = 'completed'
                                                    
                                                    )
                payments.save()
            
                print('Doing payment --------')
                user_id = RetrieveBackofficeUser().retrieve_backoffice_user(drivers.id)
                notifications = Notifications.objects.create( 
                                                    sender = user_id,  
                                                    recipient = drivers , 
                                                    notification_type ='withdraw_wallet', 
                                                    message = f"Toya has just recovered the amount of {amout_to_send_to_app} for the recent course ", 
                                                    event_id = payments.id,
                                                    )
                
                notifications.save()
                            
            else : 
                print(Exception )
                raise Exception("Transfer failed, recharge your wallet")

        except Exception as e : 
            print(e)
            raise Exception("Transfer failed, recharge your wallet")
        