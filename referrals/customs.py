from drivers.models import Drivers 
from clients.models import Clients
from referrals.models import ReferralsDrivers , ReferralsClient
from notifications.models import Notifications
from notifications.custums import RetrieveBackofficeUser
from payments.models import PaymentsDrivers
from core.utils.translations import get_message
from core.utils.language import get_user_language


class ReferralsEarnings:
    def __init__(self) -> None:
        pass

    def redistribution_of_referrals_earnings_for_driver(self, referred_driver_id: str):
        """
        Redistributes sponsorship earnings for a referred driver.
        
        Args:
            referred_driver_id (str): ID of the referred driver.

        Raises:
            ValueError: If no referral is found for the given ID.
            PermissionError: If the referral coupon has already been used.
        """
        try:
            referrals = ReferralsDrivers.objects.get(referred_driver_id=referred_driver_id)

            if referrals.used:
                raise PermissionError(
                    f"The referral coupon for the driver with ID {referred_driver_id} has already been used."
                )
            
            earning_amount = referrals.referral_bonus
            referrer_driver = Drivers.objects.get(id=str(referrals.referrer_driver_id))
            
            referrer_driver.wallet_money += earning_amount
            referrer_driver.save()
            
            payments = PaymentsDrivers.objects.create( 
                                                driver_id  = referrer_driver , 
                                                amount     = earning_amount , 
                                                payments_type = 'driver_subscription', 
                                                payments_status = 'completed'
                                                
                                                )
            payments.save()
            

            referrals.used = True
            referrals.save()
            
            # WHEN PAYEMENT WHOSE FINE
            payments = PaymentsDrivers.objects.create( 
                                                driver_id  = referrer_driver , 
                                                amount     = earning_amount , 
                                                payments_type = 'referral_earning', 
                                                payments_status = 'completed'
                                                
                                                )
            payments.save()

            user_id = RetrieveBackofficeUser().retrieve_backoffice_user(referrer_driver)
            Notifications.objects.create(
                sender=user_id,
                recipient=referrer_driver,
                notification_type='referral_earning',
                message=get_message("referral_earning", get_user_language, amount=earning_amount)
            )

            return f"Redistribution of earnings successfully carried out for the driver with ID {referred_driver_id}."

        except ReferralsDrivers.DoesNotExist:
            raise ValueError(f"No referral found for the driver with ID {referred_driver_id}.")
        except Drivers.DoesNotExist:
            raise ValueError(f"No driver found with ID {referrals.referrer_driver_id}.")

    

    def pay_referral_bonuses_after_first_ride(client_id: str, ride_id: str):
        """
        Paie 500 FCFA au parrain et 500 FCFA au parrainé
        après la première course réussie du parrainé.
        
        PROBLÈME: Les clients n'ont PAS de wallet_money.
        SOLUTION: Créer notification + stocker comme crédit futur.
        """
        from referrals.models import ReferralsClient
        from clients.models import Clients
        from notifications.models import Notifications
        from core.utils.notifications import send_notification_with_push
        from decimal import Decimal
        
        try:
            referral = ReferralsClient.objects.get(
                referred_client_id=client_id,
                first_ride_completed=False
            )
        except ReferralsClient.DoesNotExist:
            return
        
        referral.first_ride_completed = True
        referral.save()
        
        bonus_amount = Decimal(str(referral.referral_bonus_amount))
        
        # 1. PAYER LE PARRAIN
        if not referral.bonus_paid_to_referrer:
            referrer = referral.referrer_client_id
            
            send_notification_with_push(
                sender=None,
                recipient=referrer,
                notification_type='referral_bonus',
                message_key='referral_earning',
                event_id=str(ride_id)
            )
            
            referral.bonus_paid_to_referrer = True
            referral.save()
        
        # 2. PAYER LE PARRAINÉ
        if not referral.bonus_paid_to_referred:
            referred = referral.referred_client_id
            
            send_notification_with_push(
                sender=None,
                recipient=referred,
                notification_type='referral_bonus',
                message_key='referral_earning',
                event_id=str(ride_id)
            )
            
            referral.bonus_paid_to_referred = True
            referral.save()