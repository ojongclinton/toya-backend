from rest_framework import serializers 
from .models import Rides , ReviewRating



class RideClientRequestSerializer(serializers.Serializer) : 
    
    PAYMENT_MODE = [
        ('orange_money', 'Orange Money'),
        ('mtn_money', 'MTN Mobile Money'),
        ('cash', 'Paiement en espèces'),
    ]
    
    code_promo           = serializers.CharField(required=False)
    lon_start_location   = serializers.FloatField()
    lat_start_location   = serializers.FloatField()
    lon_end_location     = serializers.FloatField()
    lat_end_location     = serializers.FloatField()
    prestation           = serializers.CharField()
    mode_of_payments     = serializers.ChoiceField(choices=PAYMENT_MODE , required=True) 
    start_location       = serializers.CharField()
    end_location        = serializers.CharField()
    
    
    

class RideClientRequestsSerializer(serializers.ModelSerializer) : 
    class Meta : 
        model  = Rides 
        fields = ['id', 'client_id', 'start_location', 'end_location' , 'prestation',  'distance','final_price', "lon_start_location", "lon_end_location", "lat_start_location", "lat_end_location",'mode_of_payments', 'accepted_time', 'start_time', 'end_time']
        read_only_fields =['id', ]
        
        
        def create(self, validated_data): 
            
            rides= Rides.objects.create(**validated_data)
            rides.save()
            return rides
        
        
        
class RidesEstimateamountSerializer(serializers.Serializer) : 
    code_promo           = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    lon_start_location   = serializers.FloatField()
    lat_start_location   = serializers.FloatField()
    lon_end_location     = serializers.FloatField()
    lat_end_location     = serializers.FloatField()
    

class RidesDriverSerializer(serializers.Serializer) : 
    driver_id = serializers.CharField()
    
    
    
    

class ReviewRatingSerializer(serializers.ModelSerializer) : 
    class Meta : 
        
        model = ReviewRating
        fields = ['id', 'rides_id','client_id', 'driver_id' , 'rating' , 'comment'] 
        read_only_fields = ['create_at', 'id']
        
        
    def create(self, validated_data) : 
        
        reviews = ReviewRating.objects.create(**validated_data)
        reviews.save()
        
        return validated_data
    
    def validate_rating(self, value ) : 
        
        if value < 1 or value > 5 : 
            
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        
        return value 
    
    
    
    
class CurrentRideClientSerializer(serializers.ModelSerializer) : 
    is_price_promotion = serializers.BooleanField()
    code_promo = serializers.CharField()

    class Meta : 
        model  = Rides 
        fields = ['id','start_location', 'end_location' , 'prestation',  'distance','final_price' , 'is_price_promotion', 'code_promo' , "lon_start_location", "lon_end_location", "lat_start_location", "lat_end_location", 'accepted_time', 'start_time', 'end_time']
        read_only_fields =['id',]
        
        
        
class DriverDistanceSerializer(serializers.Serializer):
    driver_id = serializers.CharField(source='driver.id') 
    driver_name = serializers.CharField(source='driver.name') 
    distance = serializers.FloatField()  
