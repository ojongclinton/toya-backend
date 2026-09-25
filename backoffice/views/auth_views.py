
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes , parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from datetime import  timedelta

from backoffice.tasks import email_forgot_password_task
from clients.customs import OTP
from core.models import BaseUser, PasswordResetCode
from core.utils.communication import Communication
from ..models import BackofficeAdmin 
from ..serializers import *  
from drf_spectacular.utils  import extend_schema
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser , MultiPartParser
from drivers.serializers import UpdateUserProfile
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from ..permissions import IsBackofficeAdmin

@extend_schema(
    tags=['BackOffice Authentification'], 
    request= BackofficeAdminSerializer, 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )

@api_view(['POST'])
@permission_classes([IsBackofficeAdmin])
def register_admin(request):
    """
    Create a new admin user.
    
    Args:
        request: The request containing the admin user details.

    Returns:
        Response: A response containing the admin user details or an error message.
    """
    serializer = BackofficeAdminSerializer(data=request.data)
    if serializer.is_valid():
        admin_user = serializer.save()
        content = {"Message":"setting up an administrator" ,
                    'Id':admin_user.id, 
                   'Tokens':JWT.get_tokens_for_user(admin_user), 
                  
                   }
        
        return Response(data=content, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    tags=['BackOffice Authentification'], 
    request={
            'application/json': {
                'properties': {
                    'email': {'type': 'string', 'example': 'john.doe@exemple.com'},
                    'password': {'type': 'string', 'example': 'password'},
                }
            }
    }, 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )

@api_view(['POST'])
def login_admin(request):
    """
    Authenticate an admin user and return a token.

    Args:
        request: The request containing the login credentials.

    Returns:
        Response: A response containing the authentication token or an error message.
    """
    password = request.data.get('password')
    email = request.data.get('email')

    try : 
        user = BackofficeAdmin.objects.get(email = email)
    except Exception : 
        
        content  = {"Message":"User does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    if user.check_password(password) :
        
        content = {"Message":"User Logged in successfully" ,  'Id':user.id, "Tokens":JWT.get_tokens_for_user(user)}
        
        return Response(data = content , status = status.HTTP_200_OK)
    else : 
        content = {"Message":"Wrong password"}
        
        return Response(data = content , status = status.HTTP_400_BAD_REQUEST)
    
    

@extend_schema(
    tags=['BackOffice Authentification'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_admin(request, admin_id):
    """
    Delete an admin user by ID.

    Args:
        request: The request object.
        admin_id: The ID of the admin user to delete.

    Returns:
        Response: A response indicating success or failure.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        admin_user = BackofficeAdmin.objects.get(id=admin_id)
        admin_user.delete()
        content = {"Message":"Admin Delete Successfully"}
        return Response(data=content,  status=status.HTTP_200_OK)
    except BackofficeAdmin.DoesNotExist:
        return Response({'error': 'Admin not found.'}, status=status.HTTP_404_NOT_FOUND)

@extend_schema(
    tags=['BackOffice Authentification'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_admins(request):
    """
    Retrieve a list of all admin users.

    Args:
        request: The request object.

    Returns:
        Response: A response containing the list of admin users.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    admins = BackofficeAdmin.objects.all()
    serializer = ApplicationAdminDetailsSerializer(admins, many=True)
    return Response(serializer.data , status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Authentification'], 
    request={
        'application/json': {
             'properties': {
                'refresh': {'type': 'string', 'example': 'refresh_token'}
            }
        }
    },
responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_admin(request) :
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    refresh_token = request.data['refresh']
    try : 
        IsBlock = JWT.process_block_token(refresh_token)
    except Exception as e : 
        content = {"Message":f"{e}"}
        return Response(data = content , status = status.HTTP_400_BAD_REQUEST) 
    
    content = {"Message":"User Logout  successfully"}
    return Response(data = content , status = status.HTTP_200_OK) 





@extend_schema(
    tags=['BackOffice Authentification'], 
    request=UpdateUserProfile, 
    responses={
                200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
                400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
                404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_backoffice_profile_picture(request):
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        backoffice = BackofficeAdmin.objects.get(id=users.id)
    except BackofficeAdmin.DoesNotExist:
        return Response({"Message": "Admin Not Found"}, status=status.HTTP_404_NOT_FOUND)

    
    user_profile = request.data
    serializer = UpdateUserProfile(data = user_profile)
    
    if serializer.is_valid(): 
        backoffice.profile_picture = serializer.validated_data['profile_picture']
        backoffice.save()

        
        return Response({
            "Message": "Profile picture uploaded successfully", 
            "Profile Picture URL": request.build_absolute_uri(backoffice.profile_picture.url)
        }, status=status.HTTP_200_OK)
        
    return Response({"Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)







@extend_schema(
    tags=['BackOffice Authentification'], 
     request={
        'application/json': {
            'properties': {
                'email': {'type': 'string', 'example': 'john.doe@exemple.com'},
            }
        }
    },
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
def forgot_password(request) :

    email = request.data.get("email", None)
    clients = get_object_or_404(BackofficeAdmin ,email = email )
    
    email_forgot_password_task.delay(user_id=clients.id)
    
    content = {"Message":"OTP Was  send successfully" }

    return Response(data = content , status = status.HTTP_200_OK) 









@extend_schema(
    tags=['BackOffice Authentification'], 
    request={
        'application/json': {
             'properties': {
                'new_password': {'type': 'string', 'example': 'new_password'},
            }
        }
    },
    responses={
                200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
                400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
                404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_password(request):
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    new_password = request.data.get('new_password')
    user = BackofficeAdmin.objects.get(id = users.id)

    if not  PasswordResetCode.objects.get(user =  users.id ).is_valided  :
        return Response({"Message":"Action Required: Validate Your Email Before Resetting Your Password"}, status=status.HTTP_400_BAD_REQUEST)

    
    user = BackofficeAdmin.objects.get(id = users.id) 
    user.set_password(new_password)
    user.save()   
    
    return Response({"message": "Password was changed successfully", "Tokens":JWT.get_tokens_for_user(user)}, status=status.HTTP_200_OK)
    





@extend_schema(
    tags=['BackOffice Authentification'], 
    request=ValidateResetCodeBackofficeSerializer, 
    responses={
                200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
                400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
                404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['POST'])
def validate_reset_code_backoffce(request):
    user_email = request.data.get('email')
    reset_code = request.data.get('otp_code')


    user = get_object_or_404(BaseUser , email=user_email )

    try:
        reset_code_obj = PasswordResetCode.objects.get(user=user)
        
        
        if reset_code_obj.is_valided : 
            return Response({"Message": "This validation code has already been used. Please request a new one if needed."}, status=status.HTTP_400_BAD_REQUEST)
        else : 
            if reset_code_obj.reset_code == reset_code:
                if now() - reset_code_obj.created_at <= timedelta(minutes=15):
                    reset_code_obj.is_valided = True
                    reset_code_obj.save()
                    
                    return Response({"message": "Code validated. You can reset the password." , "Id":user.id ,  "Tokens":JWT.get_tokens_for_user(user)}, status=status.HTTP_200_OK)
                else:
                    return Response({"Message": "Code expired."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"Message": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)


    except PasswordResetCode.DoesNotExist:
        return Response({"Message": "No reset code found for this user."}, status=status.HTTP_404_NOT_FOUND)


