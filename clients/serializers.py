from rest_framework import serializers 
from .models import Clients
import re

class UsersSerializer(serializers.ModelSerializer):
    class Meta : 
        model = Clients 
        fields = ['id','username', 'email', 'password', 'first_name', 'last_name', 'phone_number', 'adresse', 'date_joined', 'updated_at', 'is_phone_verified']
        write_only_fields = ['password']
        read_only_fields = ['id', 'date_joined', 'updated_at', 'is_phone_verified']
        
    def create(self, validated_data) : 
        
        user = Clients.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        
        return user
    
    def validate_phone_number(self, value) : 
        pattern = r"^\+2376\d{8}$"
        
        if not re.match(pattern, value) : 
            raise serializers.ValidationError("Invalid phone number. It should start with +2376 and be followed by 9 digits.")
        return value
    
    
    def validate_password(self, value):
        
        if len(value) < 8 : 
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        return value
        
    
    
    
class ResetPasswordUsersSerializer(serializers.Serializer): 
    user_id = serializers.CharField()
    password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True) 
    
    def validate(self, data):
        user_id = data.get('user_id')
        password = data.get('password')
        new_password = data.get('new_password')

        try:
            print(user_id)
            user = Clients.objects.get(id=user_id)
        except Clients.DoesNotExist:
            raise serializers.ValidationError({"Client Id": "User does not exist"})

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Current password is not valid"})

        if password == new_password:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the old password"})

        return data

    def save(self):
        user_id = self.validated_data.get('user_id')
        new_password = self.validated_data.get('new_password')

        user = Clients.objects.get(id=user_id)
        user.set_password(new_password)
        user.save()
        
        return user
            
    
class ProfileUsersSerializer(serializers.ModelSerializer): 
    class Meta : 
        model = Clients
        fields = ["id", 'username', 'email' , 'first_name', 'last_name', 'phone_number', 'adresse','date_joined' ,'referral_code', 'is_phone_verified']
        read_only_fields = ['date_joined', 'referral_code', 'is_phone_verified']



class ValidateResetCodeClientsSerializer(serializers.Serializer): 
    phone_number = serializers.CharField(write_only=True) 
    otp_code = serializers.CharField(write_only=True)


class RequestSignupOTPSerializer(serializers.Serializer):
    """Serializer for requesting/resending signup OTP."""
    phone_number = serializers.CharField(write_only=True)
    
    def validate_phone_number(self, value):
        pattern = r"^\+2376\d{8}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError("Invalid phone number. It should start with +2376 and be followed by 8 digits.")
        return value


class VerifySignupOTPSerializer(serializers.Serializer):
    """Serializer for verifying signup OTP."""
    phone_number = serializers.CharField(write_only=True)
    otp_code = serializers.CharField(write_only=True, min_length=6, max_length=6)
    
    def validate_phone_number(self, value):
        pattern = r"^\+2376\d{8}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError("Invalid phone number. It should start with +2376 and be followed by 8 digits.")
        return value 