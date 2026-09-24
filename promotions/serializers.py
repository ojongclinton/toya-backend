from rest_framework import serializers
from .models import Promotions


class PromotionsSerializer(serializers.ModelSerializer): 
    class Meta : 
        model = Promotions 
        fields = ['id' , 'code' , 'discount_percentage', 'description',  'start_date', 'end_date', 'status', 'usage_limit' ]
        read_only_fields= ['id',]
        


        
class PromotionClientAppliedSerializer(serializers.Serializer): 
    promotion_id = serializers.CharField()
