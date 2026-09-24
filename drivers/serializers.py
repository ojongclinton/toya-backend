from rest_framework import serializers
from django.db import models
from .models import Drivers, Vehicle, Grade
import re

class DriversUsersSerializer(serializers.ModelSerializer):
    class Meta : 
        model = Drivers 
        fields = ['id', 'username', 'email' , 'password', 'first_name', 'last_name', 'phone_number', 'adresse', 'is_phone_verified']
        read_only_fields = ['id', 'is_phone_verified']
        
    def create(self, validated_data) : 
        
        user = Drivers.objects.create(**validated_data)
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
            user = Drivers.objects.get(id=user_id)
        except Drivers.DoesNotExist:
            raise serializers.ValidationError({"Drivers Id": "User does not exist"})

        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Current password is not valid"})

        if password == new_password:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the old password"})

        return data

    def save(self):
        user_id = self.validated_data.get('user_id')
        new_password = self.validated_data.get('new_password')

        user = Drivers.objects.get(id=user_id)
        user.set_password(new_password)
        user.save()
        
        return user
            
    
class DriversProfileUsersSerializer(serializers.ModelSerializer): 
    class Meta : 
        model = Drivers
        fields = ["id", 'username', 'email' , 'first_name', 'last_name', 'phone_number', 'adresse' ,  'date_joined' , 'referral_code', 'is_phone_verified', 'wallet_money']
        read_only_fields = [  'email'  , 'date_joined' , 'referral_code', 'is_phone_verified', 'wallet_money']


class NearbyDriversForARideProfileSerializer(serializers.ModelSerializer):
    """Serializer pour les chauffeurs proches (avec véhicule)"""
    
    vehicle = serializers.SerializerMethodField()
    
    class Meta:
        model = Drivers
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'profile_picture',
            'vehicle',  # Ajout du véhicule avec photo
        ]
    
    def get_vehicle(self, obj):
        """Récupère les détails du véhicule"""
        try:
            vehicle = Vehicle.objects.get(driver_id=obj)
            return VehicleDetailsSerializer(vehicle).data
        except Vehicle.DoesNotExist:
            return None



class VehicleDriverSerializer (serializers.Serializer) : 
    driver_id               = serializers.CharField()
    vehicle_brand           = serializers.CharField() 
    vehicle_model           = serializers.CharField()
    license_plate           = serializers.CharField()
    vehicle_color = serializers.ChoiceField(choices=Vehicle.VEHICLE_COLORS, default='purple')
    
    prestation = serializers.ChoiceField(choices=Vehicle.TYPE_OF_PRESTATION, default='economy')
    photos                  = serializers.ImageField()
    vehicle_rental_contract = serializers.ImageField()
    driving_licence_front   = serializers.ImageField()
    driving_licence_back    = serializers.ImageField()
    insurrance_file         = serializers.ImageField()
    criminal_record_certificate = serializers.FileField(required=False, allow_null=True)
    technical_control_document = serializers.FileField(required=False, allow_null=True)
    
   
    def create(self, validated_data):
        try : 
            driver = Drivers.objects.get(id=validated_data.get('driver_id'))
            validated_data['driver_id'] = driver
        except Drivers.DoesNotExist:
            raise serializers.ValidationError("Driver Does not Exist")
        
        try : 
            vehicle = Vehicle.objects.create(**validated_data)
            vehicle.save()
        except Exception  as e : 
            raise serializers.ValidationError(e)
        return validated_data


    def update(self, instance, validated_data):
        instance.vehicle_brand = validated_data.get('vehicle_brand', instance.vehicle_brand)
        instance.vehicle_model = validated_data.get('vehicle_model', instance.vehicle_model)
        instance.license_plate = validated_data.get('license_plate', instance.license_plate)
        instance.vehicle_color = validated_data.get('vehicle_color', instance.vehicle_color)
        instance.prestation = validated_data.get('prestation', instance.prestation)

        if 'photos' in validated_data:
            instance.photos = validated_data['photos']
        if 'vehicle_rental_contract' in validated_data:
            instance.vehicle_rental_contract = validated_data['vehicle_rental_contract']
        if 'driving_licence_front' in validated_data:
            instance.driving_licence_front = validated_data['driving_licence_front']
        if 'driving_licence_back' in validated_data:
            instance.driving_licence_back = validated_data['driving_licence_back']
        if 'insurrance_file' in validated_data:
            instance.insurrance_file = validated_data['insurrance_file']
        if 'criminal_record_certificate' in validated_data:
            instance.criminal_record_certificate = validated_data['criminal_record_certificate']
        if 'technical_control_document' in validated_data:
            instance.technical_control_document = validated_data['technical_control_document']

        instance.save()
        return instance
    
    
class VehicleDetailsSerializer(serializers.ModelSerializer):
    """Serializer pour retourner les détails du véhicule (pour le client)"""
    
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'vehicle_brand',
            'vehicle_model',
            'license_plate',
            'vehicle_color',
            'prestation',
            'photos',
        ]
        read_only_fields = ['id']   

        
class DriverProfileForClientSerializer(serializers.ModelSerializer):
    """Serializer pour le profil chauffeur visible par le client (avec véhicule)"""
    
    vehicle = serializers.SerializerMethodField()
    
    class Meta:
        model = Drivers
        fields = [
            'id',
            'first_name',
            'last_name',
            'phone_number',
            'profile_picture',  # Photo du chauffeur
            'vehicle',  # Détails du véhicule (avec photo)
        ]
        read_only_fields = ['id']
    
    def get_vehicle(self, obj):
        """Récupère les détails du véhicule associé au chauffeur"""
        try:
            vehicle = Vehicle.objects.get(driver_id=obj)
            return VehicleDetailsSerializer(vehicle).data
        except Vehicle.DoesNotExist:
            return None

        
class UpdateUserProfile(serializers.Serializer) : 
    profile_picture         = serializers.ImageField()
    
    
    
    
class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'
        read_only_fields = ['id']


class SubscriptionDepositSeriaizer(serializers.Serializer): 
    amount = serializers.IntegerField()
    payment_method = serializers.CharField()
    
    
    
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
    # otp_code = serializers.CharField(write_only=True) 



# ---- GRADES

"""
Serializers for the grade management system.
"""
from rest_framework import serializers
from drivers.models import Grade, GradeRequirement, DriverGrade
from django.utils import timezone


class GradeSerializer(serializers.ModelSerializer):
    """Serializer for the Grade model."""
    
    class Meta:
        model = Grade
        fields = [
            'id',
            'name',
            'commission_rate',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_commission_rate(self, value):
        """Validate that the commission rate is between 0 and 100."""
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Commission rate must be between 0 and 100.")
        return value


class GradeRequirementSerializer(serializers.ModelSerializer):
    """Serializer for the GradeRequirement model."""
    
    requirement_type_display = serializers.CharField(
        source='get_requirement_type_display',
        read_only=True
    )
    
    comparison_operator_display = serializers.CharField(
        source='get_comparison_operator_display',
        read_only=True
    )
    
    class Meta:
        model = GradeRequirement
        fields = [
            'id',
            'grade',
            'requirement_type',
            'requirement_type_display',
            'comparison_operator',
            'comparison_operator_display',
            'value',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'requirement_type_display',
            'comparison_operator_display'
        ]
    
    def validate(self, attrs):
        """
        Validate that the requirement is valid.
        - Ensures the comparison operator is valid for the requirement type.
        - Validates the value based on the requirement type.
        """
        requirement_type = attrs.get('requirement_type')
        comparison_operator = attrs.get('comparison_operator')
        value = attrs.get('value')
        
        # Validate comparison operator
        valid_operators = ['>=', '>', '==']
        if comparison_operator not in valid_operators:
            raise serializers.ValidationError({
                'comparison_operator': f'Must be one of {valid_operators}.'
            })
        
        # Validate value based on requirement type
        try:
            if requirement_type in [GradeRequirement.RATING]:
                value = float(value)
                if not (0 <= value <= 5):
                    raise serializers.ValidationError({
                        'value': 'Rating must be between 0 and 5.'
                    })
            elif requirement_type in [GradeRequirement.RIDES_COUNT, GradeRequirement.REFERRALS]:
                value = int(value)
                if value < 0:
                    raise serializers.ValidationError({
                        'value': 'Must be a non-negative integer.'
                    })
            elif requirement_type == GradeRequirement.REVENUE:
                value = float(value)
                if value < 0:
                    raise serializers.ValidationError({
                        'value': 'Revenue must be a non-negative number.'
                    })
        except (ValueError, TypeError):
            raise serializers.ValidationError({
                'value': 'Invalid value for the specified requirement type.'
            })
        
        # Update the validated value
        attrs['value'] = str(value)
        return attrs


class DriverGradeSerializer(serializers.ModelSerializer):
    """Serializer for the DriverGrade model."""
    
    grade_name = serializers.CharField(source='grade.name', read_only=True)
    commission_rate = serializers.DecimalField(
        source='grade.commission_rate',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = DriverGrade
        fields = [
            'id',
            'driver',
            'grade',
            'grade_name',
            'commission_rate',
            'assigned_at',
            'unassigned_at',
            'is_current',
            'reason'
        ]
        read_only_fields = [
            'id',
            'grade_name',
            'commission_rate',
            'assigned_at',
            'unassigned_at',
            'is_current'
        ]
    
    def validate_grade(self, value):
        """Validate that the grade is active."""
        if not value.is_active:
            raise serializers.ValidationError("Cannot assign an inactive grade.")
        return value


class DriverGradeProgressSerializer(serializers.Serializer):
    """Serializer for driver grade progression data."""
    
    current_grade = GradeSerializer(read_only=True)
    next_grade = GradeSerializer(read_only=True, allow_null=True)
    progress_percentage = serializers.FloatField(min_value=0, max_value=100)
    requirements = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            allow_empty=True
        )
    )
    all_requirements_met = serializers.BooleanField()
    
    class Meta:
        fields = [
            'current_grade',
            'next_grade',
            'progress_percentage',
            'requirements',
            'all_requirements_met'
        ]


class GradeBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating driver grades."""
    
    driver_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    
    def validate_driver_ids(self, value):
        """Validate that all driver IDs exist."""
        from drivers.models import Drivers
        
        if not value:
            raise serializers.ValidationError("At least one driver ID is required.")
        
        existing_drivers = set(
            Drivers.objects.filter(id__in=value).values_list('id', flat=True)
        )
        
        missing_drivers = set(value) - existing_drivers
        if missing_drivers:
            raise serializers.ValidationError(
                f"The following driver IDs do not exist: {', '.join(str(id) for id in missing_drivers)}"
            )
        
        return value
