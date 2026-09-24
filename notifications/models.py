from django.db import models
from core.models import BaseUser
from uuid import uuid4
    
class Notifications(models.Model):
    NOTIFICATION_TYPES = (
        
        ('payment_success', 'Payment_success'),
        ('payment_failed', 'Payment_failed'),
        ('ride_canceled', 'Ride_canceled'),
        ('new_ride', 'NewRide'),
        ('ride_started', 'Ride_started'),
        ('ride_accepted', 'Ride_accepted'),
        ('ride_completed', 'Ride_completed'),
        ('withdraw_wallet', 'Withdraw_wallet'),
        ('recharge_wallet', 'Recharge_wallet'),
        ('course_available', 'Course_available'), 
        ('support_ticket', 'Support_ticket'), 
        ('referral', 'referral'), 
        ('referral_earning', 'referral_earning'), 
        ('vehicle_submission_for_verification', 'vehicle_submission_for_verification'), 
        ("subscription_payment", "subscription_payment"), 
        ('message_received', "message_received"), 
        ('support_message_received', "support_message_received"), 
        ('documents_rejected', 'documents_rejected'),
        ('documents_approved', 'documents_approved'),
        
    )

    id                  = models.URLField(primary_key=True , unique=True, default=uuid4)
    sender              = models.ForeignKey(BaseUser, related_name="notification_from", on_delete=models.CASCADE )
    recipient           = models.ForeignKey(BaseUser, related_name="notification_to", on_delete=models.CASCADE)
    notification_type   = models.CharField(max_length=255, choices=NOTIFICATION_TYPES)
    message             = models.TextField(blank=True)
    is_read             = models.BooleanField(default=False)
    timestamp           = models.DateTimeField(auto_now_add=True)
    event_id            = models.CharField(max_length=255, blank=True, null=True) 

    
    def __str__(self) -> str:
        return f'Notification from {self.sender} to {self.recipient}'

    
    def mark_as_read(self): 
        self.is_read = True
        self.save()