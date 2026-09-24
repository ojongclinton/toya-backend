from rest_framework import serializers
from .models import ReferralsClient, ReferralsDrivers

# class ReferralsClientSerializer(serializers.Serializer): 
class ReferralsClientSerializer(serializers.ModelSerializer): 
    class Meta:
        model = ReferralsClient
        fields = ['id', 'referrer_client_id', 'referred_client_id', 'referral_bonus', 'used', 'created_at']
        read_only_fields = ['id', 'created_at']

class ReferralsDriversSerializer(serializers.ModelSerializer): 
    class Meta:
        model = ReferralsDrivers
        fields = ['id', 'referrer_driver_id', 'referred_driver_id', 'referral_bonus', 'used', 'created_at']
        read_only_fields = ['id', 'created_at']

class ReferralsClientInviteSerializer(serializers.Serializer): 
    invite_referral_code = serializers.CharField()
        

# class ReferralsDriversSerializer(serializers.ModelSerializer): 
class ReferralsDriversInviteSerializer(serializers.Serializer): 
    invite_referral_code = serializers.CharField()