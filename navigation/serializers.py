from rest_framework import serializers
from .models import Position, PositionHistory

class LastPositionOfDriver(serializers.ModelSerializer): 
    class Meta: 
        model = Position
        fields = ['id', 'user_id', 'lat', 'lon', 'address']
        read_only_fields = ['id']

    def create(self, validated_data):
        return Position.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class PositionHistorySerializer(serializers.ModelSerializer): 
    class Meta: 
        model = PositionHistory
        fields = ['id', 'user_id', 'lat', 'lon', 'address', 'timestamp']
        read_only_fields = ['id', 'timestamp']

    def create(self, validated_data):
        return PositionHistory.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class AvailableDriverSerializer(serializers.Serializer):
    """Serializer pour les chauffeurs disponibles sur la carte"""
    driver_id = serializers.UUIDField(source='id')
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
    profile_picture = serializers.ImageField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    vehicle_brand = serializers.CharField()
    vehicle_model = serializers.CharField()
    license_plate = serializers.CharField()
    vehicle_color = serializers.CharField()
    prestation = serializers.CharField()
    distance_km = serializers.FloatField(required=False)
    grade = serializers.CharField()
    rating = serializers.FloatField()


class HotZoneSerializer(serializers.Serializer):
    """Serializer pour les zones chaudes"""
    zone_id = serializers.CharField()
    center_lat = serializers.FloatField()
    center_lon = serializers.FloatField()
    rides_count = serializers.IntegerField()
    density_level = serializers.CharField()  # 'high' (violet) ou 'low' (blanc)
    radius_km = serializers.FloatField()