from rest_framework import serializers 
from .models import SupportTicket , Fag , SupportsConversation
from rides.models import Rides

class SupportTicketClientSerializer(serializers.ModelSerializer) : 
    ride_details = serializers.SerializerMethodField(read_only=True)
    ride_id = serializers.PrimaryKeyRelatedField(
        source='ride', 
        queryset=Rides.objects.all(), 
        required=False, 
        allow_null=True,
        error_messages={
            'does_not_exist': 'The specified ride does not exist.',
            'invalid': 'Invalid ride ID format.'
        }
    )
    
    class Meta : 
        model = SupportTicket 
        fields = ['id', 'users_id', 'ride_id', 'ride_details', 'issue_description' , 'type_user', 'status', 'created_at']
        read_only_fields = ['status' ,'id', 'created_at', 'ride_details']
    
    def get_ride_details(self, obj):
        if obj.ride:
            return {
                'id': str(obj.ride.id),
                'driver_id': str(obj.ride.driver_id.id) if obj.ride.driver_id else None,
                'client_id': str(obj.ride.client_id.id) if obj.ride.client_id else None,
                'driver_name': f"{obj.ride.driver_id.first_name} {obj.ride.driver_id.last_name}" if obj.ride.driver_id else None,
                'client_name': f"{obj.ride.client_id.first_name} {obj.ride.client_id.last_name}" if obj.ride.client_id else None,
                'start_location': obj.ride.start_location,
                'end_location': obj.ride.end_location,
                'status': obj.ride.status,
                'final_price': obj.ride.final_price,
                'start_time': obj.ride.start_time
            }
        return None
        
    def create(self,validated_data) : 
        support = SupportTicket.objects.create(**validated_data)
        support.type_user = 'client'
        support.save() 
        
        return support 
    

class SupportTicketdDriversSerializer(serializers.ModelSerializer) : 
    ride_details = serializers.SerializerMethodField(read_only=True)
    ride_id = serializers.PrimaryKeyRelatedField(
        source='ride', 
        queryset=Rides.objects.all(), 
        required=False, 
        allow_null=True,
        error_messages={
            'does_not_exist': 'The specified ride does not exist.',
            'invalid': 'Invalid ride ID format.'
        }
    )
    
    class Meta : 
        model = SupportTicket 
        fields = ['id', 'users_id', 'ride_id', 'ride_details', 'issue_description' , 'type_user', 'status', 'created_at']
        read_only_fields = ['status' , 'id' , 'created_at', 'ride_details']
    
    def get_ride_details(self, obj):
        if obj.ride:
            return {
                'id': str(obj.ride.id),
                'driver_id': str(obj.ride.driver_id.id) if obj.ride.driver_id else None,
                'client_id': str(obj.ride.client_id.id) if obj.ride.client_id else None,
                'driver_name': f"{obj.ride.driver_id.first_name} {obj.ride.driver_id.last_name}" if obj.ride.driver_id else None,
                'client_name': f"{obj.ride.client_id.first_name} {obj.ride.client_id.last_name}" if obj.ride.client_id else None,
                'start_location': obj.ride.start_location,
                'end_location': obj.ride.end_location,
                'status': obj.ride.status,
                'final_price': obj.ride.final_price,
                'start_time': obj.ride.start_time
            }
        return None
        
    def create(self,validated_data) : 
        support = SupportTicket.objects.create(**validated_data)
        support.type_user = 'drivers'
        support.save() 
        
        return support 
    

class FagSerializer(serializers.ModelSerializer): 
    class Meta : 
        model = Fag
        fields = ['id','question' , 'answers', 'type_user', 'created_at']
        read_only_fields = ['id', 'created_at']
        
        
class SupportTicketFieldsSerializer(serializers.Serializer) : 
    issue_description = serializers.CharField()
    ride_id = serializers.UUIDField(required=False, allow_null=True)
    
    
    
    
class SupportConversationSerializer(serializers.ModelSerializer): 
    class Meta : 
        model = SupportsConversation
        fields = ['id', 'sender_id','receiver_id' , 'ticket_id' , 'message', 'created_at', 'is_read']
        read_only_fields = ['id', 'created_at']
        
        
    def create(self, validated_data) : 
        
        conversation = SupportsConversation.objects.create(**validated_data)
        conversation.save()
        
        return validated_data
