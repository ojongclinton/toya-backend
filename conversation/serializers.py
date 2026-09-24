from rest_framework import serializers 
from .models import Conversation

class ConversationSerializer(serializers.ModelSerializer): 
    class Meta : 
        model = Conversation
        fields = ['id', 'sender_id','receiver_id' , 'rides_id' , 'message', 'timestamp', 'is_read']
        read_only_fields = ['id', 'timestamp']
        
        
    def create(self, validated_data) : 
        
        conversation = Conversation.objects.create(**validated_data)
        conversation.save()
        
        return validated_data
        
        