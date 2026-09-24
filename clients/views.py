from rest_framework.decorators import api_view , permission_classes , parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from clients.tasks import notifiy_new_user_with_sms_tasks
from .serializers import *
from drivers.serializers import UpdateUserProfile
from core.models import PasswordResetCode
from rest_framework import status
from .models import Clients
from .customs import OTP, SignupOTPManager
from .customs import JWT
from core.throttling import OTPRequestThrottle, OTPVerifyThrottle
from drf_spectacular.utils import extend_schema
from rides.models import Rides , ReviewRating
from django.db.models import Avg , Sum
from rest_framework.parsers import FormParser , MultiPartParser
from datetime import  timedelta
from django.utils.timezone import now

import re
import os
import requests
from core.sms.service import SMSClient
from dotenv import load_dotenv

load_dotenv()


@extend_schema(
    tags=['Clients'],
    request={
        'application/json': {
            'properties': {
                'phone_number': {'type': 'string', 'example': '+237697200000'},
                'message': {'type': 'string', 'example': 'Hello from TOYA test endpoint'}
            },
            'required': ['phone_number', 'message']
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'Message': {'type': 'string', 'example': 'Test SMS sent successfully.'},
                'ProviderResponse': {'type': 'string'}
            }
        },
        400: {'type': 'object', 'properties': {'Message': {'type': 'string'}}},
        500: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}
    }
)
@api_view(['POST'])
def test_sms(request:Request, *args, **kwargs) -> Response:
    """
    Sends a test SMS using the configured SMS provider via `core.sms.service.SMSClient`.
    Accepts JSON body: {"phone_number": "+2376XXXXXXXX", "message": "..."}
    """
    phone_number = request.data.get("phone_number")
    client = Clients.objects.get(phone_number = phone_number)
    # message = request.data.get("message")

    if not phone_number :
        return Response({"Message": "Both 'phone_number' and 'message' are required."}, status=status.HTTP_400_BAD_REQUEST)

    # Enforce local phone format used elsewhere in the API
    pattern = r"^\+2376\d{8}$"
    if not re.match(pattern, phone_number):
        return Response({"Message": "Invalid phone number. It should start with +2376 and be followed by 9 digits."}, status=status.HTTP_400_BAD_REQUEST)

    otp = OTP().generate_otp(client)
    # otp = 123456
    # message = f"Votre code de validation est : {otp}"
    print(otp)
    message = "{}: TOYA Vtc Votre code de validation est : {}".format(os.environ.get("SMS_SENDER_ID"), otp)


    sms_client = SMSClient()
    # Ensure environment variables are available
    if not all([sms_client.user, sms_client.password, sms_client.sender_id]):
        return Response({"Message": "SMS credentials are not configured. Please set SMS_USER, SMS_PASSWORD, and SMS_SENDER_ID."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    provider_response = sms_client.send_sms(message=message, mobile_number=phone_number)

    if provider_response is None:
        return Response({"Message": "Failed to send SMS. Check logs for provider error details."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"Message": "Test SMS sent successfully.", "ProviderResponse": provider_response}, status=status.HTTP_200_OK)

@extend_schema(
     tags=['Clients'], 
    request=UsersSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
def register_client(request:Request, *args, **kwargs) : 
    from django.conf import settings
    
    client_data = request.data 
    
    serializer = UsersSerializer(data = client_data)
    
    if serializer.is_valid(): 
        user = serializer.save()
        
        # Feature flag: conditionally enforce phone verification
        if settings.ENFORCE_PHONE_VERIFICATION:
            # New flow: send OTP, don't issue tokens yet
            otp = SignupOTPManager.generate_signup_otp(user)
            message = f"Votre code de validation TOYA est : {otp}. Valide 15 minutes."
            notifiy_new_user_with_sms_tasks.delay(str(user.phone_number), message)
            
            content = {
                "Message": "Signup initiated. Please verify the code sent to your phone.",
                "Id": user.id,
                "verification_required": True
            }
            return Response(data=content, status=status.HTTP_200_OK)
        else:
            # Legacy flow: issue tokens immediately (backward compatible)
            content = {
                "Message": "User created successfully",
                'Id': user.id, 
                'Tokens': JWT.get_tokens_for_user(user),
            }
            message = f"Bienvenue chez TOYA.\nCommandez votre premier trajet en 2 clics.\n\nPrix fixe, service de qualité, zéro stress.\nLe VTC comme il se doit.\n\n {os.getenv('SMS_SENDER_ID')}"
            notifiy_new_user_with_sms_tasks.delay(str(user.phone_number), message)
            
            return Response(data=content, status=status.HTTP_200_OK)
    else : 
        content = {"Message": serializer.errors}
        
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)


 
@extend_schema(
     tags=['Clients'], 
    request={
        'application/json': {
             'properties': {
                'phone_number': {'type': 'string', 'example': '+237697200000'},
                'password': {'type': 'string', 'example': 'yourpassword'}
            }
        }
    },
    responses={
        200: {
            'properties': {
                'Message': {'type': 'string', 'example': 'User logged in successfully'},
                'Tokens': {
                    'properties': {
                        'access': {'type': 'string', 'example': 'access_token'},
                        'refresh': {'type': 'string', 'example': 'refresh_token'}
                    }
                }
            }
        },
        400: {'properties': {'Message': {'type': 'string', 'example': 'Incorrect password.'}}},
        403: {'properties': {'Message': {'type': 'object', 'example': {'Message': 'Phone number not verified. Please verify your phone to continue.' , "Id": "<user_id>" , "verification_required": True}}}},
        404: {'properties': {'Message': {'type': 'string', 'example': 'User does not exist.'}}}
    }
)

@api_view(['POST'])
def login_client(request:Request, *args, **kwargs) :
    from django.conf import settings
    
    client_data = request.data
    try : 
        user = Clients.objects.get(phone_number = client_data['phone_number'])
    except Exception : 
        
        content  = {"Message":"User does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    if user.check_password(client_data['password']) :
        # Feature flag: conditionally check phone verification
        if settings.ENFORCE_PHONE_VERIFICATION and not user.is_phone_verified:
            content = {
                "Message": "Phone number not verified. Please verify your phone to continue.",
                "verification_required": True,
                "Id": user.id
            }
            return Response(data=content, status=status.HTTP_403_FORBIDDEN)
        
        content = {"Message":"The user has successfully logged in" ,  'Id':user.id, "Tokens":JWT.get_tokens_for_user(user)}
        
        return Response(data = content , status = status.HTTP_200_OK)
    else : 
        content = {"Message":"Wrong password"}
        
        return Response(data = content , status = status.HTTP_400_BAD_REQUEST)
    



@extend_schema(
    tags=['Clients'], 
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
    user = Clients.objects.get(id = users.id)

    if not  PasswordResetCode.objects.get(user =  users.id ).is_valided  :
        return Response({"Message":"Action Required: Validate Your Email Before Resetting Your Password"}, status=status.HTTP_400_BAD_REQUEST)

    
    user = Clients.objects.get(id = users.id) 
    user.set_password(new_password)
    user.save()   
    
    return Response({"message": "Password was changed successfully", "Tokens":JWT.get_tokens_for_user(user)}, status=status.HTTP_200_OK)
    




@extend_schema(
    tags=['Clients'], 
    request={
        'application/json': {
            'properties': {
                'phone_number': {'type': 'string', 'example': '+237697200000'},
            }
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'Message': {'type': 'string', 'example': 'OTP sent successfully'},
                'OTP': {'type': 'string'},
                'ProviderResponse': {'type': 'string'}
            }
        },
        400: {'type': 'object', 'properties': {'Message': {'type': 'string'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string'}}},
        500: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}
    }
)
@api_view(['POST'])
def forgot_password(request:Request, *args, **kwargs) -> Response:
    """
    Sends an OTP via SMS for password reset using the configured SMS provider.
    Accepts JSON body: {"phone_number": "+2376XXXXXXXX"}
    """
    phone_number = request.data.get("phone_number", None)
    
    if not phone_number:
        return Response({"Message": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        client = Clients.objects.get(phone_number=phone_number)
    except Clients.DoesNotExist:
        return Response({"Message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Generate OTP first
    otp = OTP().generate_otp(client)
    message = f"Votre code de validation est : {otp}\n\n {os.getenv('SMS_SENDER_ID')}"
    
    # Use Celery task to send SMS (isolates database operations from SMS service)
    notifiy_new_user_with_sms_tasks.delay(str(client.phone_number), message)
    
    # return Response({"Message": "OTP sent successfully", "OTP": otp}, status=status.HTTP_200_OK) 
    # print(f"OTP sent successfully to phone - Code : {otp}")
    # Security: Do not return OTP in response, only send via SMS.
    # Edit: Return OTP in response for testing purposes. The app is still in development and we need to test the OTP verification process.
    return Response({"Message": "OTP sent successfully to your phone.", "OTP": otp}, status=status.HTTP_200_OK) 



@extend_schema(
    tags=['Clients'], 
    request=ValidateResetCodeClientsSerializer, 
    responses={
                200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
                400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
                404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['POST'])
def validate_reset_code_clients(request):
    user_phone_number = request.data.get('phone_number')
    reset_code = request.data.get('otp_code')

    try:
        user = Clients.objects.get(phone_number=user_phone_number)
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


    except Clients.DoesNotExist:
        return Response({"Message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except PasswordResetCode.DoesNotExist:
        return Response({"Message": "No reset code found for this user."}, status=status.HTTP_404_NOT_FOUND)






@extend_schema(
    tags=['Clients'], 
    request={
        'application/json': {
             'properties': {
                'refresh': {'type': 'string', 'example': 'refresh_token'}
            }
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'Message': {'type': 'string', 'example': 'User Logout successfully'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'Message': {'type': 'string', 'example': 'Invalid refresh token'}
            }
        }
    }
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_client(request):
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        return Response({"Message": "Refresh token is missing."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        JWT().process_block_token(refresh_token)

        content = {"Message": "User logout successfully. Token has been invalidated."}
        return Response(data=content, status=status.HTTP_200_OK)
    
    except Exception as e:
        content = {"Message": f"An error occurred: {str(e)}"}
        return Response(data=content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







@extend_schema(
     tags=['Clients'], 
    request=ProfileUsersSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    if request.method == 'GET' : 
        
        
        serializer = ProfileUsersSerializer(users)
        
        
        user_id = serializer.data['id']
        
        profile_picture = Clients.objects.get(id = user_id).profile_picture or None
        
        if profile_picture : 
            profile_picture = request.build_absolute_uri(profile_picture.url) 
        else : 
            profile_picture = None

        
        
        content = {"Message":"User Informations", 'Tokens':token,  'Data':serializer.data ,"profile_picture":profile_picture }
        
        return Response(data = content , status = status.HTTP_200_OK)
    
    if request.method == 'PUT' : 

        username = request.data.get('username', None)
        first_name = request.data.get('first_name',None)
        last_name = request.data.get('last_name',None)
        phone_number = request.data.get('phone_number',None)
        adresse = request.data.get('adresse',None)

        driver = Clients.objects.get(id = users.id)

        if username:
            driver.username = username
        if first_name:
            driver.first_name = first_name
        if last_name:
            driver.last_name = last_name
        if phone_number:
            
            pattern = r"^\+2376\d{8}$"
        
            if not re.match(pattern, phone_number) : 
                content = {"Message": "Invalid phone number. It should start with +2376 and be followed by 9 digits.", 'Tokens': token}
                return Response(data = content , status = status.HTTP_400_BAD_REQUEST)
            
            driver.phone_number = phone_number
            
        if adresse:
            driver.adresse = adresse
            
        driver.save()
        
        content = {"Message": "User Updated Successfully", 'Tokens': token}
        return Response(data = content , status = status.HTTP_200_OK)
    
    
@extend_schema(
    tags=['Clients'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stats_client(request: Request, *args, **kwargs): 
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    try: 
        client = Clients.objects.get(id=users.id)
        
        # Filtrer seulement les courses COMPLETED
        rides = Rides.objects.filter(
            client_id=client,
            status='completed'
        )
  
        total_rides_counts = rides.count() or 0
        
        average_rating = ReviewRating.objects.filter(client_id=client).aggregate(Avg('rating'))['rating__avg'] or 0 
        
        # Total dépensé seulement sur courses completed
        total_spent = Rides.objects.filter(
            client_id=client,
            status='completed'
        ).aggregate(Sum('final_price'))['final_price__sum'] or 0
        
        content = {
            "Message": "Client Stats", 
            "Data": {
                'client_id': client.id,
                'total_rides': total_rides_counts,  
                'total_spent': total_spent, 
                'average_rating': round(average_rating, 2)
            }
        }
        
        return Response(data=content, status=status.HTTP_200_OK)
        
    except Clients.DoesNotExist: 
        content = {"Message": "Client Does Not Exist"}
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)
    

@extend_schema(
    tags=['Clients'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_client(request:Request) : 
    """
    Permanently delete client account and all related data.
    Handles cascade deletion of rides, payments, support tickets, etc.
    """
    from django.conf import settings
    
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Safety guard: only allow when testing endpoints are enabled
    if not settings.ENABLE_TESTING_ENDPOINTS:
        return Response(
            {"Message": "Account deletion is disabled. Please contact support."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try : 
        client = Clients.objects.get(id=users.id)
        
        # Delete related data explicitly to avoid cascade issues
        from rides.models import Rides, ReviewRating
        from payments.models import PaymentsClients
        from support.models import SupportTicket, SupportsConversation
        from conversation.models import Conversation
        from notifications.models import Notifications
        from referrals.models import ReferralsClient
        from promotions.models import ApplyPromotions
        
        # Delete all related records
        Rides.objects.filter(client_id=client).delete()
        ReviewRating.objects.filter(client_id=client).delete()
        PaymentsClients.objects.filter(client_id=client).delete()
        SupportTicket.objects.filter(users_id=client).delete()
        SupportsConversation.objects.filter(sender_id=client).delete()
        SupportsConversation.objects.filter(receiver_id=client).delete()
        Conversation.objects.filter(sender_id=client).delete()
        Conversation.objects.filter(receiver_id=client).delete()
        Notifications.objects.filter(sender=client).delete()
        Notifications.objects.filter(recipient=client).delete()
        ReferralsClient.objects.filter(referrer_client_id=client).delete()
        ReferralsClient.objects.filter(referred_client_id=client).delete()
        ApplyPromotions.objects.filter(client_id=client).delete()
        
        # Finally delete the client
        client.delete()
        
        content = {"Message":"Client account and all related data deleted successfully"}
        return Response(data = content , status = status.HTTP_200_OK)
    except Clients.DoesNotExist : 
        content = {"Message":"Client Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        content = {"Message": f"Error deleting account: {str(e)}"}
        return Response(data=content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    

    
@extend_schema(
    tags=['Clients'], 
    request=UpdateUserProfile, 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_clients_profile_picture(request):
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        client = Clients.objects.get(id=users.id)
    except Clients.DoesNotExist:
        return Response({"Message": "Clients Not Found"}, status=status.HTTP_404_NOT_FOUND)

    
    user_profile = request.data
    serializer = UpdateUserProfile(data = user_profile)
    
    if serializer.is_valid(): 
        client.profile_picture = serializer.validated_data['profile_picture']
        client.save()


        return Response({
            "Message": "Profile picture uploaded successfully", 
            "Profile Picture URL": request.build_absolute_uri(client.profile_picture.url) 
        }, status=status.HTTP_200_OK)
        
    return Response({"Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Clients'],
    request=RequestSignupOTPSerializer,
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'OTP sent successfully'}}},
        400: {'type': 'object', 'properties': {'Message': {'type': 'string'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'User not found'}}},
        429: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Too many requests'}}}
    }
)
@api_view(['POST'])
@permission_classes([])
def request_signup_otp(request: Request) -> Response:
    """
    Request or resend signup OTP for phone verification.
    Rate limited to x requests per hour per phone number. (ex. 5 requests per hour per phone number)
    """
    # Apply throttling
    throttle = OTPRequestThrottle()
    if not throttle.allow_request(request, None):
        return Response(
            {"Message": "Too many OTP requests. Please try again later."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    serializer = RequestSignupOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number = serializer.validated_data['phone_number']
    
    try:
        user = Clients.objects.get(phone_number=phone_number)
    except Clients.DoesNotExist:
        return Response({"Message": "User not found. Please register first."}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if already verified
    if user.is_phone_verified:
        return Response({"Message": "Phone number already verified."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate and send OTP
    otp = SignupOTPManager.generate_signup_otp(user)
    message = f"Votre code de validation TOYA est : {otp}. Valide 15 minutes."
    
    # Send via Celery task
    notifiy_new_user_with_sms_tasks.delay(str(user.phone_number), message)
    
    # Edit: Return OTP in response for testing purposes. The app is still in development and we need to test the OTP verification process.
    return Response({"Message": "OTP sent successfully to your phone.", "OTP": otp}, status=status.HTTP_200_OK) 


@extend_schema(
    tags=['Clients'],
    request=VerifySignupOTPSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'Message': {'type': 'string', 'example': 'Phone verified successfully'},
                'Id': {'type': 'string'},
                'Tokens': {
                    'properties': {
                        'access': {'type': 'string'},
                        'refresh': {'type': 'string'}
                    }
                }
            }
        },
        400: {'type': 'object', 'properties': {'Message': {'type': 'string'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string'}}},
        429: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}
    }
)
@api_view(['POST'])
@permission_classes([])
def verify_signup_otp(request: Request) -> Response:
    """
    Verify signup OTP and mark phone as verified.
    Returns JWT tokens on success.
    Rate limited default to 10 requests per hour per phone number.
    """
    # Apply throttling
    throttle = OTPVerifyThrottle()
    if not throttle.allow_request(request, None):
        return Response(
            {"Message": "Too many verification attempts. Please try again later."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    serializer = VerifySignupOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number = serializer.validated_data['phone_number']
    otp_code = serializer.validated_data['otp_code']
    
    try:
        user = Clients.objects.get(phone_number=phone_number)
    except Clients.DoesNotExist:
        return Response({"Message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if already verified
    if user.is_phone_verified:
        return Response(
            {
                "Message": "Phone already verified. You can log in.",
                "Id": user.id,
                "Tokens": JWT.get_tokens_for_user(user)
            },
            status=status.HTTP_200_OK
        )
    
    # Validate OTP
    success, message = SignupOTPManager.validate_signup_otp(user, otp_code)
    
    if not success:
        return Response({"Message": message}, status=status.HTTP_400_BAD_REQUEST)
    
    # Mark phone as verified
    user.is_phone_verified = True
    user.save()
    
    # Return tokens
    return Response(
        {
            "Message": "Phone verified successfully. You can now log in.",
            "Id": user.id,
            "Tokens": JWT.get_tokens_for_user(user)
        },
        status=status.HTTP_200_OK
    )


# ==================== DEVELOPMENT/TESTING ENDPOINTS ====================

@extend_schema(
    tags=['Clients - Development'],
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}},
        403: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_client_account(request: Request) -> Response:
    """
    **DEVELOPMENT ONLY**: Reset client account to initial state.
    Clears all related data (rides, payments, support tickets, etc.) but keeps the account.
    Useful for frontend testing without re-registering.
    """
    from django.conf import settings
    
    # Safety guard: only allow when testing endpoints are enabled
    if not settings.ENABLE_TESTING_ENDPOINTS:
        return Response(
            {"Message": "This endpoint is only available when ENABLE_TESTING_ENDPOINTS is True."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        client = Clients.objects.get(id=users.id)
        
        # Import all related models
        from rides.models import Rides, ReviewRating
        from payments.models import PaymentsClients
        from support.models import SupportTicket, SupportsConversation
        from conversation.models import Conversation
        from notifications.models import Notifications
        from referrals.models import ReferralsClient
        from promotions.models import ApplyPromotions
        from core.models import PasswordResetCode, SignupOTP
        
        # Clear all related data
        Rides.objects.filter(client_id=client).delete()
        ReviewRating.objects.filter(client_id=client).delete()
        PaymentsClients.objects.filter(client_id=client).delete()
        SupportTicket.objects.filter(users_id=client).delete()
        SupportsConversation.objects.filter(sender_id=client).delete()
        SupportsConversation.objects.filter(receiver_id=client).delete()
        Conversation.objects.filter(sender_id=client).delete()
        Conversation.objects.filter(receiver_id=client).delete()
        Notifications.objects.filter(sender=client).delete()
        Notifications.objects.filter(recipient=client).delete()
        ReferralsClient.objects.filter(referrer_client_id=client).delete()
        ReferralsClient.objects.filter(referred_client_id=client).delete()
        ApplyPromotions.objects.filter(client_id=client).delete()
        PasswordResetCode.objects.filter(user=client).delete()
        SignupOTP.objects.filter(user=client).delete()
        
        # Reset account flags
        client.is_phone_verified = False
        client.save()
        
        return Response(
            {
                "Message": "Client account reset successfully. All related data cleared.",
                "Details": {
                    "phone_verified": False,
                    "account_status": "reset"
                }
            },
            status=status.HTTP_200_OK
        )
        
    except Clients.DoesNotExist:
        return Response(
            {"Message": "Client not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"Message": f"Error resetting account: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

