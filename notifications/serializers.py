from rest_framework import serializers 
from .models import Notifications

class NotificationsSerializer(serializers.ModelSerializer) : 
    class Meta : 
        model = Notifications
        fields = ['id', 'sender','recipient' , 'notification_type', 'message', 'is_read', 'timestamp', 'event_id']
        read_only_fields =['id', 'timestamp']