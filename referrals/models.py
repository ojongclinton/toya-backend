from django.db import models
from uuid import uuid4

class ReferralsClient(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, null=False, default=uuid4)
    referrer_client_id = models.ForeignKey('clients.clients', on_delete=models.CASCADE, related_name="referrals_as_referrer")
    referred_client_id = models.OneToOneField('clients.clients', on_delete=models.CASCADE, unique=True, related_name="referrals_as_referred")
    
    # NOUVEAU SYSTÈME (500 FCFA fixe)
    referral_bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    bonus_paid_to_referrer = models.BooleanField(default=False)
    bonus_paid_to_referred = models.BooleanField(default=False)
    first_ride_completed = models.BooleanField(default=False)
    
    # ANCIEN SYSTÈME (gardé pour compatibilité)
    referral_bonus = models.IntegerField(default=50)
    used = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.id)


class ReferralsDrivers(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, null=False, default=uuid4)
    referrer_driver_id = models.ForeignKey('drivers.drivers', on_delete=models.CASCADE, related_name="referrals_as_referrer")
    referred_driver_id = models.OneToOneField('drivers.drivers', on_delete=models.CASCADE, unique=True, related_name="referrals_as_referred", null=True, blank=True)
    
    # NOUVEAU SYSTÈME
    referral_bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    bonus_paid_to_referrer = models.BooleanField(default=False)
    bonus_paid_to_referred = models.BooleanField(default=False)
    first_ride_completed = models.BooleanField(default=False)
    
    # ANCIEN SYSTÈME
    referral_bonus = models.IntegerField(default=20)
    used = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.id)