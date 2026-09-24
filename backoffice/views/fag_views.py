from rest_framework import status 
from rest_framework.response import Response 
from rest_framework.request import Request 
from rest_framework.decorators import api_view , permission_classes 
from support.models import Fag  
from ..serializers import * 
from drf_spectacular.utils import extend_schema
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated


@extend_schema(
    tags=['BackOffice Fag'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_all_fag(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    fag = Fag.objects.all()
    serializer = FagSerializer(fag ,many=True)
    
    content = {"Message":'All Fag', "Data":serializer.data}
    
    return Response(data=content , status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Fag'], 
    request=FagSerializer ,
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['POST']) 
@permission_classes([IsAuthenticated])
def create_fag(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    data = request.data 
    
    serializer = FagSerializer(data = data)
    
    if serializer.is_valid(): 
        serializer.save()
        
        return Response(data = {"Message":"Fag created"} , status=status.HTTP_200_OK)
    
    return Response(data = {"Message":serializer.errors} , status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    tags=['BackOffice Fag'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_details_of_fag(request:Request , fag_id :str , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))


    try : 
        fag = Fag.objects.get(id = fag_id)
        serializer = FagSerializer(fag)
        
    except Exception as e : 
        content  = {"Message":"Fag does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    content = {"Message":'Fag details',"Data":serializer.data}
    return Response(data=content , status=status.HTTP_200_OK)
    
    
    
@extend_schema(
    tags=['BackOffice Fag'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_fag(request:Request, fag_id:str ,  *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try : 
        fag = Fag.objects.get(id = fag_id)
        print("pass")        
    except Fag.DoesNotExist : 
        content  = {"Message":"Fag does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    print("pass")
    fag.delete()
    print("pass")
    content = {"Message":'This Fag has been deleted'}
    return Response(data=content , status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Fag'], 
    request=FagSerializer, 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_fag(request:Request ,fag_id :str,  *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try : 
        fag = Fag.objects.get(id = fag_id)
    except Fag.DoesNotExist : 
        content  = {"Message":"Fag does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    question = request.data.get('question', None)
    answers = request.data.get('answers',None)
    type_user = request.data.get('type_user',None)

    
    if question:
        fag.question = question
    if answers:
        fag.answers = answers
    if type_user:
        fag.type_user = type_user


    fag.save()

    
    content = {"Message": "Fag Updated Successfully",}
    return Response(data = content , status = status.HTTP_200_OK)
