from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notifications
from rides.models import Rides


@receiver(post_save, sender=Notifications)
def send_notification_to_websocket(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()


        additional_data = {}
        
        if instance.notification_type in ['ride_started', 'ride_accepted', 'ride_completed']:
            event_id = f'{instance.event_id}'  
            if instance.notification_type == 'ride_accepted' : 
                rides_id = Rides.objects.get(id=event_id)
                additional_data['rides_drivers_closed']  = str(rides_id.driver_id.id)             
            
        elif instance.notification_type in ['payment_success', 'payment_failed', 'subscription_payment']:
            event_id = f'{instance.id}' 
            
        elif instance.notification_type == 'ride_canceled':
            event_id = f'{instance.id}'  
            
        elif instance.notification_type == 'new_ride':
            event_id = f'{instance.id}' 
            
        elif instance.notification_type == 'support_ticket':
            event_id = f'{instance.id}' 
        else:
            
            event_id = None

        notification_data = {
            'type': 'send_notification',
            'message': instance.message,
            'event_id': event_id,
            "notification_type" : instance.notification_type, 
            "additional_data": additional_data
        }

        async_to_sync(channel_layer.group_send)(
            f'notifications_{instance.recipient.id}',
            notification_data
        )
