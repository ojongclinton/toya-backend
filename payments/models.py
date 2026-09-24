from django.db import models
from uuid import uuid4
from decimal import Decimal
from drivers.models import * 

class PaymentsDrivers(models.Model): 
    PAYMENT_METHOD = [ 
                      ("orange_money", "Orange_money"), 
                      ("mtn_money", "Mtn_money"), 
                      ("credit_card", "credit_card"),                       
                      ]
    STATUS          = [ 
                       
                      ("in_pending", "In_pending"), 
                      ("completed", "Completed"), 
                      ("cancelled", "Cancelled"),      
                           ("failed", "Failed")
                       ]
    
    PAYMENT_TYPE          = [ 
                       
                      ("wallet_pay", "wallet_pay"),
                      ("referral_earning", "referral_earning"),     
                      ('driver_subscription', 'driver_subscription' ), 
                      ("ride_payment", "ride_payment")
                       
                       ]
    
    
    id                  = models.UUIDField(primary_key=True , default=uuid4 , unique=True) 
    driver_id           = models.ForeignKey('drivers.drivers', on_delete=models.CASCADE)
    amount              = models.FloatField() 
    payments_method     = models.CharField(max_length=255 , null=False , default='orange_money' ,  choices=PAYMENT_METHOD)
    payments_status     = models.CharField(max_length=255 , null=False , choices=STATUS , default="in_pending")
    payments_type       = models.CharField(max_length=255 , null=False , choices=PAYMENT_TYPE , default="wallet_pay")
    # commission          = models.IntegerField() 
    created_at           = models.DateTimeField(auto_now_add=True)
    
 

class PaymentsClients(models.Model): 
    PAYMENT_METHOD = [ 
                      ("orange_money", "Orange_money"), 
                      ("mtn_money", "Mtn_money"), 
                      ("credit_card", "credit_card"),  
                      ]
    
    STATUS          = [ 
                       
                      ("in_pending", "In_pending"), 
                      ("completed", "Completed"), 
                      ("cancelled", "Cancelled"),      
                       
                       ]
    
    id                  = models.UUIDField(primary_key=True , default=uuid4 , unique=True) 
    client_id           = models.ForeignKey('clients.clients', on_delete=models.CASCADE)
    rides_id            = models.OneToOneField('rides.rides', null=True,  on_delete=models.CASCADE )
    amount              = models.FloatField(null=False) 
    phone_number        = models.CharField(max_length=255 , null=False)
    payments_method     = models.CharField(max_length=255 , null=False , choices=PAYMENT_METHOD , default='orange_money')
    payments_status     = models.CharField(max_length=255 , null=False , choices=STATUS , default="in_pending")
    created_at           = models.DateTimeField(auto_now_add=True)
    

    
    def __str__(self) : 
        return  str(self.id)






class PaymentPhoneNumber(models.Model):
    id                  = models.UUIDField(primary_key=True , default=uuid4 , unique=True) 
    driver              = models.ForeignKey(Drivers, on_delete=models.CASCADE, related_name='payment_numbers')
    phone_number        = models.CharField(max_length=20)
    created_at          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


TRANSACTION_TYPE = [
    # Money IN
    ("deposit", "Wallet Deposit"),
    ("ride_earning", "Ride Earning"),
    ("referral_bonus", "Referral Bonus"),
    ("admin_credit", "Admin Credit"),
    
    # Money OUT
    ("commission_deduction", "Commission Deduction"),
    ("subscription_fee", "Subscription Fee"),
    ("penalty", "Penalty"),
    ("admin_debit", "Admin Debit"),
]

TRANSACTION_STATUS = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]


class WalletTransaction(models.Model):
    """
    Records all wallet transactions for drivers.
    Provides audit trail and enables balance reconciliation.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)
    driver = models.ForeignKey(
        'drivers.Drivers', 
        on_delete=models.CASCADE, 
        related_name='wallet_transactions'
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    
    # References
    ride = models.ForeignKey(
        'rides.Rides', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='wallet_transactions'
    )
    payment = models.ForeignKey(
        'PaymentsDrivers', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    
    # Metadata
    description = models.TextField(blank=True)
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Commission rate at time of transaction"
    )
    grade_name = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Driver grade at time of transaction"
    )
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=TRANSACTION_STATUS, 
        default='pending'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['driver', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.driver.id} - {self.transaction_type} - {self.amount} FCFA"
