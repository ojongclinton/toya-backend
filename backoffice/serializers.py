from rides.models import Rides 
from rest_framework.serializers import ModelSerializer 
from promotions.models import Promotions , ApplyPromotions
from rest_framework import serializers
from support.models import Fag
from referrals.models import ReferralsClient , ReferralsDrivers
from support.models import SupportTicket
from support.serializers import SupportTicketClientSerializer as SupportClientSerializer
from support.serializers import SupportTicketdDriversSerializer as SupportDriverSerializer
from .models import BackofficeAdmin
from payments.models import PaymentsClients , PaymentsDrivers



class RidesSerializer(ModelSerializer) : 
    class Meta :
        model = Rides
        fields = "__all__"

class PromotionsSerializer(ModelSerializer) : 
    class Meta :
        model = Promotions
        fields = "__all__"
        
    def create(self , validated_date): 
        
        promotions = Promotions.objects.create(**validated_date)
        promotions.save()
        
        return validated_date
        
        
        
class ApplyPromotionsSerializer(ModelSerializer) : 
    class Meta :
        model = ApplyPromotions
        fields = "__all__"
        
        

class FagSerializer(ModelSerializer): 
    class Meta :
        model = Fag
        fields = "__all__"
        read_only_fields =['id']
        
    def create(self , validated_date): 
        
        promotions = Fag.objects.create(**validated_date)
        promotions.save()
        
        return validated_date
    
    
    def validate(self, attrs):
        type_user = attrs.get('type_user')

        if type_user not in ['client', 'drivers']:
            raise serializers.ValidationError({
                "type_user": "Type must be either 'client' or 'driver'."
            })
        
        return attrs
    
    
    
class ReferralsClientSerializer(ModelSerializer) : 
    class Meta :
        model = ReferralsClient
        fields = "__all__"
        
        
        
class ReferralsDriversSerializer(ModelSerializer) : 
    class Meta :
        model = ReferralsDrivers
        fields = "__all__"
        
        
# Import des serializers depuis support/ pour éviter la duplication
SupportTicketClientSerializer = SupportClientSerializer
SupportTicketDriverSerializer = SupportDriverSerializer
        
class BackofficeAdminSerializer(ModelSerializer) : 
    
    class Meta:
        model = BackofficeAdmin
        fields = ('email', 'password', 'username', 'first_name', 'last_name', 'phone_number')

    def create(self, validated_data):
        user = BackofficeAdmin(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'],
            user_type    = 'admin'
        )
        user.set_password(validated_data['password'])  
        user.save()
        return user
    
    
class ApplicationAdminDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackofficeAdmin
        fields = ['id', 'email', "phone_number", 'user_type', 'is_active', 'is_staff', 'date_joined']
        
        
        
        

class  PaymentsClientsSerializer(ModelSerializer):
    class Meta: 
        model = PaymentsClients
        fields = '__all__'
class PaymentsDriversSerializer (ModelSerializer):
    class Meta: 
        model = PaymentsDrivers
        fields = '__all__'
    




class ValidateResetCodeBackofficeSerializer(serializers.Serializer): 
    email = serializers.CharField(write_only=True) 
    otp_code = serializers.CharField(write_only=True) 