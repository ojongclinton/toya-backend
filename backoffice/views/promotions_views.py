from rest_framework import status 
from rest_framework.response import Response 
from rest_framework.request import Request 
from rest_framework.decorators import api_view , permission_classes 
from promotions.models import Promotions , ApplyPromotions 
from ..serializers import * 
from drf_spectacular.utils import extend_schema
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated
from datetime import datetime , timedelta


@extend_schema(
    tags=['BackOffice Promotions'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_all_promotions(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    promotions = Promotions.objects.all()
    serializer = PromotionsSerializer(promotions ,many=True)
    
    content = {"Message":'All Promotions', "Data":serializer.data}
    
    return Response(data=content , status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Promotions'], 
    request={
        'application/json': {
            'type': 'object',
          'properties': {
                'code': {'type': 'string', 'example': 'PROMO2024', 'description': 'Unique promotional code'},
                'discount_percentage': {'type': 'number', 'example': 20, 'description': 'Discount percentage'},
                'description': {'type': 'string', 'example': 'End of year discount', 'description': 'Promotion description'},
                'start_date': {'type': 'string', 'format': 'date-time', 'example': f'{datetime.now()}', 'description': 'Start date and time of the promotion (ISO 8601)'},
                'end_date': {'type': 'string', 'format': 'date-time', 'example': f'{datetime.now() + timedelta(days=30)}', 'description': 'End date and time of the promotion (ISO 8601)'},
                "usage_limit" :  {'type': 'number', 'example': 200, 'description': 'usage limit of code'},
            },
        }
    },
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['POST']) 
@permission_classes([IsAuthenticated])
def create_promotion(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    data = request.data 
    
    serializer = PromotionsSerializer(data = data)
    
    if serializer.is_valid(): 
        serializer.save()
        
        return Response(data = {"Message":"Promotion created"} , status=status.HTTP_200_OK)
    
    return Response(data = {"Message":serializer.errors} , status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    tags=['BackOffice Promotions'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_details_of_promotions(request:Request , promotions_id :str , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        promotions = Promotions.objects.get(id = promotions_id)
        serializer = PromotionsSerializer(promotions)
        
    except Exception as e : 
        content  = {"Message":"Promotions does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    content = {"Message":'Promotions details',"Data":serializer.data}
    return Response(data=content , status=status.HTTP_200_OK)
    
    
    
@extend_schema(
    tags=['BackOffice Promotions'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_promotions(request:Request, promotions_id:str ,  *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try : 
        promotions = Promotions.objects.get(id = promotions_id)        
    except Promotions.DoesNotExist : 
        content  = {"Message":"Promotions does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    promotions.delete()
    
    content = {"Message":'This Promotions has been deleted'}
    return Response(data=content , status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Promotions'], 
    request={
        'application/json': {
            'type': 'object',
          'properties': {
                'code': {'type': 'string', 'example': 'PROMO2024', 'description': 'Unique promotional code'},
                'discount_percentage': {'type': 'number', 'example': 20, 'description': 'Discount percentage'},
                'description': {'type': 'string', 'example': 'End of year discount', 'description': 'Promotion description'},
                'start_date': {'type': 'string', 'format': 'date-time', 'example': '2024-12-01T08:00:00Z', 'description': 'Start date and time of the promotion (ISO 8601)'},
                'end_date': {'type': 'string', 'format': 'date-time', 'example': '2024-12-31T23:59:59Z', 'description': 'End date and time of the promotion (ISO 8601)'},
            },
        }
    },
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_promotion(request:Request ,promotions_id :str,  *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try : 
        promotions = Promotions.objects.get(id = promotions_id)
    except Promotions.DoesNotExist : 
        content  = {"Message":"Promotions does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    code = request.data.get('code', None)
    discount_percentage = request.data.get('discount_percentage',None)
    description = request.data.get('description',None)
    start_date = request.data.get('start_date',None)
    end_date = request.data.get('end_date',None)
    
    if code:
        promotions.code = code
    if discount_percentage:
        promotions.discount_percentage = discount_percentage
    if description:
        promotions.description = description
    if start_date:
  
        promotions.start_date = start_date
        
    if end_date:
        promotions.end_date = end_date

    promotions.save()

    
    content = {"Message": "Promotions Updated Successfully",}
    return Response(data = content , status = status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Promotions'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_client_with_applied_promotions(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    promotions = ApplyPromotions.objects.all()
    serializer = ApplyPromotionsSerializer(promotions ,many=True)
    
    content = {"Message":'All Applied Promotion', "Data":serializer.data}
    
    return Response(data=content , status=status.HTTP_200_OK)


@extend_schema(
    tags=['BackOffice Promotions'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_client_with_applied_promotions(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    promotions = ApplyPromotions.objects.all()
    serializer = ApplyPromotionsSerializer(promotions ,many=True)
    
    content = {"Message":'All Applied Promotion', "Data":serializer.data}
    
    return Response(data=content , status=status.HTTP_200_OK)

@extend_schema(
    tags=['BackOffice Promotions'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_applied_promotions_for_promotion(request:Request , promotions_id :str,  *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        
        applied_promotion = ApplyPromotions.objects.filter(promotions_id = promotions_id)
        serializer = ApplyPromotionsSerializer(applied_promotion , many=True)
    except Exception as e : 
        content  = {"Message":"Promotions does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)

    content = {"Message":'ApplyPromotions Data',"Data":serializer.data}
    return Response(data=content , status=status.HTTP_200_OK)


