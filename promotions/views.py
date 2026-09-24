from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from .models import Promotions , ApplyPromotions
from .serializers import PromotionsSerializer , PromotionClientAppliedSerializer
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from clients.customs import JWT as JWT_CLIENT 
from drf_spectacular.utils import extend_schema

@extend_schema(
      tags=['Promotions'], 
    request=PromotionsSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_active_promotion(request:Request, *args, **kwargs) :
    _ , user = JWT_CLIENT.filter_and_decode_token(request.headers.get("Authorization"))
    promotions = Promotions.objects.filter(end_date__gt =  timezone.now())
    
    serializers = PromotionsSerializer(promotions, many=True)
    
    content = {"Message":"All active Promotions", "Data":serializers.data}
    return Response( data=content , status=status.HTTP_200_OK)




@extend_schema(
      tags=['Promotions'], 
    request=PromotionClientAppliedSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_apply_for_active_promotion(request:Request , *args, **kwargs) : 
    _ , user = JWT_CLIENT.filter_and_decode_token(request.headers.get("Authorization"))
    data  = request.data 
    print(data)
    try : 
        promotion = Promotions.objects.get(id = request.data.get('promotion_id'))
    except Promotions.DoesNotExist : 
        content = {"Message":"Promotions Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    
    if promotion.end_date > timezone.now() : 
        applied = ApplyPromotions.objects.create(
            client_id = user,  
            promotions_id  = promotion
        )
        applied.save()

        
        content = {"Message":"Promotions was applied "}
        return Response(data=content , status=status.HTTP_200_OK)
    
    else : 
        content = {"Message":"Promotions is not active "}
        return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
    
    