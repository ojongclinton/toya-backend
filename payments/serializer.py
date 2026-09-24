from rest_framework import serializers 
from .models import *
import re

class PayRidesSerializer(serializers.ModelSerializer) : 
    class Meta : 
        model = PaymentsClients
        fields = ['id', 'client_id' ,'rides_id', 'amount' , 'phone_number' , 'payments_method', 'payments_status', 'created_at']
        read_only_fields = ['id', 'created_at']
        
    def create(self , validated_data): 
        
        payements = PaymentsClients.objects.create(**validated_data)
        payements.save()
        
        return validated_data




class PaymentSerializer(serializers.Serializer) : 
    rides_id = serializers.CharField()
    payments_method = serializers.CharField()
    # code_promo       = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class WalletDepositSeriaizer(serializers.Serializer) : 
    amount = serializers.IntegerField()
    payment_method = serializers.CharField()
    phone_number = serializers.CharField()
    
    
    def validate_phone_number(self, value) : 
        pattern = r"^\+2376\d{8}$"
        
        if not re.match(pattern, value) : 
            raise serializers.ValidationError("Invalid phone number. It should start with +2376 and be followed by 9 digits.")
        return value
    
    
    
class PaymentPhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPhoneNumber
        fields = ['id', 'phone_number', 'created_at'] 
        read_only_fields = ['id', 'created_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'balance_before',
            'balance_after',
            'description',
            'commission_rate',
            'grade_name',
            'status',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentsDriversSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentsDrivers
        fields = ['id', 'driver_id', 'amount', 'payments_method', 'payments_status', 'payments_type', 'created_at']
        read_only_fields = ['id', 'created_at']