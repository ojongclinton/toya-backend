import os
from asgiref.sync import async_to_sync
from rest_framework.decorators import api_view , permission_classes , parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from clients.tasks import notifiy_new_user_with_sms_tasks
from core.utils import notifications
# from core import settings
from .serializers import *
from rest_framework import status
from .models import Drivers , Vehicle , Subscription
from .customs import JWT
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser , MultiPartParser
from rides.models import Rides , ReviewRating
from django.db.models import Avg , Sum 
from .grades import DriverGrade
import re
from notifications.custums import RetrieveBackofficeUser
from django.utils import timezone
from datetime import timedelta
from referrals.customs import ReferralsEarnings
from core.models import PasswordResetCode
from django.utils.timezone import now
from clients.customs import OTP, SignupOTPManager
from payments.serializer import PaymentPhoneNumberSerializer
from core.throttling import OTPRequestThrottle, OTPVerifyThrottle
from channels.layers import get_channel_layer
from drivers.models import Vehicle

from dotenv import load_dotenv
from core.utils.notifications import send_notification_with_push

load_dotenv()


    
    

@extend_schema(
    tags=['Drivers'], 
    request=DriversUsersSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
def register_drivers(request: Request, *args, **kwargs):
    from django.conf import settings
    
    drivers_data = request.data
    serializer = DriversUsersSerializer(data=drivers_data)
   
    if serializer.is_valid(): 
        user = serializer.save()
        
        # Broadcast to backoffice
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'backoffice_notifications',
            {
                'type': 'new_driver_registration',
                'driver_id': str(user.id),
                'driver_name': f"{user.first_name} {user.last_name}",
                'phone_number': user.phone_number,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        phone_number = request.data.get('phone_number')
        if phone_number:
            phone_serializer = PaymentPhoneNumberSerializer(data={'phone_number': phone_number})
            if phone_serializer.is_valid():
                phone_serializer.save(driver=user)
        
        # Feature flag: conditionally enforce phone verification
        if settings.ENFORCE_PHONE_VERIFICATION:
            # New flow: send OTP, don't issue tokens yet
            otp = SignupOTPManager.generate_signup_otp(user)
            message = f"Votre code de verification TOYA est : {otp}. Valide 15 minutes."
            notifiy_new_user_with_sms_tasks.delay(str(user.phone_number), message)
            
            content = {
                "Message": "Signup initiated. Please verify the code sent to your phone.",
                "Id": user.id,
                "verification_required": True
            }
            return Response(data=content, status=status.HTTP_200_OK)
        else:
            # Legacy flow: issue tokens immediately (backward compatible)
            message = f"🎉 Félicitations {user.first_name}.\n\nVous êtes maintenant chauffeur chez TOYA. Liberté, revenus et reconnaissance vous attendent. Rendez-vous dans l'appli pour finaliser votre profil et commencer à rouler. TOYA croit en vous \n\n {os.getenv('SMS_SENDER_ID')}"
            notifiy_new_user_with_sms_tasks.delay(str(user.phone_number), message)
            
            content = {"Message": "User created successfully", "Id": user.id, 'Tokens': JWT.get_tokens_for_user(user)}
            return Response(data=content, status=status.HTTP_200_OK)
    else:
        content = {"Message": serializer.errors}
        return Response(data=content, status=status.HTTP_400_BAD_REQUEST)





@extend_schema(
    tags=['Drivers'], 
    request={
        'application/json': {
            'properties': {
                'phone_number': {'type': 'string', 'example': '697200000'},
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
def login_drivers(request:Request, *args, **kwargs) :
    from django.conf import settings
    
    drivers_data = request.data
    try : 
        user = Drivers.objects.get(phone_number = drivers_data['phone_number'])
    except Exception : 
        
        content  = {"Message":"User does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    if user.check_password(drivers_data['password']) :
        # Feature flag: conditionally check phone verification
        if settings.ENFORCE_PHONE_VERIFICATION and not user.is_phone_verified:
            content = {
                "Message": "Phone number not verified. Please verify your phone with OTP to continue.",
                "verification_required": True,
                "Id": user.id
            }
            return Response(data=content, status=status.HTTP_403_FORBIDDEN)
        
        content = {"Message":"User Logged in successfully" ,"Id":user.id ,  "Tokens":JWT.get_tokens_for_user(user)}
        
        return Response(data = content , status = status.HTTP_200_OK)
    else : 
        content = {"Message":"Wrong password"}
        
        return Response(data = content , status = status.HTTP_400_BAD_REQUEST)
    
    



@extend_schema(
    tags=['Drivers'], 
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
    user = Drivers.objects.get(id = users.id)

    if not  PasswordResetCode.objects.get(user =  users.id ).is_valided  :
        return Response({"Message":"Action Required: Validate Your Email Before Resetting Your Password"}, status=status.HTTP_400_BAD_REQUEST)

    
    user = Drivers.objects.get(id = users.id) 
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
                'OTP': {'type': 'string'}
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
        driver = Drivers.objects.get(phone_number=phone_number)
    except Drivers.DoesNotExist:
        return Response({"Message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
    # Generate OTP first
    otp = OTP().generate_otp(driver)
    message = f"Votre code de validation est : {otp}\n\n {os.getenv('SMS_SENDER_ID')}"
    

    # Use Celery task to send SMS (isolates database operations from SMS service)
    notifiy_new_user_with_sms_tasks.delay(str(driver.phone_number), message)
    # return Response({"Message": "OTP sent successfully", "OTP": otp}, status=status.HTTP_200_OK) 

    # Security: Do not return OTP in response, only send via SMS
    # Edit: Return OTP in response for testing purposes. The app is still in development and we need to test the OTP verification process.
    return Response({"Message": "OTP sent successfully to your phone.", "OTP": otp}, status=status.HTTP_200_OK) 



@extend_schema(
    tags=['Drivers'], 
    request=ValidateResetCodeClientsSerializer, 
    responses={
                200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
                400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
                404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['POST'])
def validate_reset_code_drivers(request):
    user_phone_number = request.data.get('phone_number')
    reset_code = request.data.get('otp_code')

    try:
        user = Drivers.objects.get(phone_number=user_phone_number)
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


    except Drivers.DoesNotExist:
        return Response({"Message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except PasswordResetCode.DoesNotExist:
        return Response({"Message": "No reset code found for this user."}, status=status.HTTP_404_NOT_FOUND)



    





@extend_schema(
    tags=['Drivers'], 
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
def logout_drivers(request):
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
    tags=['Drivers'], 
    request=DriversProfileUsersSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request:Request , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    if request.method == 'GET' : 
        serializer = DriversProfileUsersSerializer(users)
        
        user_id = serializer.data['id']
        
        profile_picture = Drivers.objects.get(id = user_id).profile_picture or None
        
        if profile_picture : 
            profile_picture = request.build_absolute_uri(profile_picture.url) 
        else : 
            profile_picture = None

        
        # Informations véhicule avec photo
        vehicle_data = None
        try:
            vehicle = Vehicle.objects.get(driver_id=users.id)
            vehicle_photo = vehicle.photos.url if vehicle.photos else None
            if vehicle_photo:
                vehicle_photo = request.build_absolute_uri(vehicle_photo)
            
            vehicle_data = {
                "vehicle_brand": vehicle.vehicle_brand,
                "vehicle_model": vehicle.vehicle_model,
                "license_plate": vehicle.license_plate,
                "vehicle_color": vehicle.vehicle_color,
                "vehicle_photo": vehicle_photo,
                "prestation": vehicle.prestation,
                "validation_status": vehicle.validation_status,
            }
        except Vehicle.DoesNotExist:
            pass  # Pas de véhicule enregistré
        
        content = {"Message":"User Informations", 'Tokens':token,  'Data':serializer.data ,"profile_picture":profile_picture,"vehicle": vehicle_data }
        
    
        return Response(data = content , status = status.HTTP_200_OK)
    
    if request.method == 'PUT' : 
        
        username = request.data.get('username', None)
        first_name = request.data.get('first_name',None)
        last_name = request.data.get('last_name',None)
        phone_number = request.data.get('phone_number',None)
        adresse = request.data.get('adresse',None)

        driver = Drivers.objects.get(id = users.id)

        if username:
            driver.username = username
        if first_name:
            driver.first_name = first_name
        if last_name:
            driver.last_name = last_name
        if phone_number:
            
            pattern = r"^\+2376\d{8}$"
        
            if not re.match(pattern, phone_number) : 
                content = {"Message": "Invalid phone number. It should start with +2376 and be followed by 9 digits."}
                return Response(data = content , status = status.HTTP_400_BAD_REQUEST)
            
            driver.phone_number = phone_number
        if adresse:
            driver.adresse = adresse
            
        driver.save()
        
        content = {"Message": "User Updated Successfully", 'Tokens': token}
        return Response(data = content , status = status.HTTP_200_OK)
    
    
  
@extend_schema(
    tags=['Drivers'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_driver(request:Request) : 
    """
    Permanently delete driver account and all related data.
    Handles cascade deletion of rides, payments, vehicles, subscriptions, etc.
    """
    from django.conf import settings
    
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Safety guard: only allow when testing endpoints are enabled
    if not settings.ENABLE_TESTING_ENDPOINTS:
        return Response(
            {"Message": "Account deletion is disabled. Please contact support."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try : 
        driver = Drivers.objects.get(id=users.id)
        
        # Delete related data explicitly to avoid cascade issues
        from rides.models import Rides, ReviewRating
        from payments.models import PaymentsDrivers, PaymentPhoneNumber
        from support.models import SupportTicket, SupportsConversation
        from conversation.models import Conversation
        from notifications.models import Notifications
        from referrals.models import ReferralsDrivers
        from drivers.models import Vehicle, Subscription
        
        # Delete all related records
        Rides.objects.filter(driver_id=driver).delete()
        ReviewRating.objects.filter(driver_id=driver).delete()
        PaymentsDrivers.objects.filter(driver_id=driver).delete()
        PaymentPhoneNumber.objects.filter(driver=driver).delete()
        SupportTicket.objects.filter(users_id=driver).delete()
        SupportsConversation.objects.filter(sender_id=driver).delete()
        SupportsConversation.objects.filter(receiver_id=driver).delete()
        Conversation.objects.filter(sender_id=driver).delete()
        Conversation.objects.filter(receiver_id=driver).delete()
        Notifications.objects.filter(sender=driver).delete()
        Notifications.objects.filter(recipient=driver).delete()
        ReferralsDrivers.objects.filter(referrer_driver_id=driver).delete()
        ReferralsDrivers.objects.filter(referred_driver_id=driver).delete()
        Vehicle.objects.filter(driver_id=driver).delete()
        Subscription.objects.filter(driver_id=driver).delete()
        
        # Finally delete the driver
        driver.delete()
        
        content = {"Message":"Driver account and all related data deleted successfully"}
        return Response(data = content , status = status.HTTP_200_OK)
    except Drivers.DoesNotExist : 
        content = {"Message":"Driver Does Not Exist"}
        return Response(data=content , status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        content = {"Message": f"Error deleting account: {str(e)}"}
        return Response(data=content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@extend_schema(
   tags=['KYC Drivers'], 
    request=VehicleDriverSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_Kyc_driver_vehicle(request: Request):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from django.utils import timezone
    
    _, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    vehicle_data = request.data
    serializer = VehicleDriverSerializer(data=vehicle_data) 
    
    if serializer.is_valid():
        data = serializer.save()
        vehicle = Vehicle.objects.get(id=data.id)
        
        # Broadcast au backoffice
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'backoffice_notifications',
            {
                'type': 'vehicle_submission',
                'driver_id': str(users.id),
                'driver_name': f"{users.first_name} {users.last_name}",
                'vehicle_brand': vehicle.vehicle_brand,
                'vehicle_model': vehicle.vehicle_model,
                'license_plate': vehicle.license_plate,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        # Récupérer admin backoffice
        try:
            backoffice_admin = RetrieveBackofficeUser().retrieve_backoffice_user(users.id)
        except:
            backoffice_admin = None
        
        driver = Drivers.objects.get(id=users.id)
        
        # Notification pour le CHAUFFEUR
        send_notification_with_push(
            sender=backoffice_admin if backoffice_admin else driver,
            recipient=driver,
            notification_type='vehicle_submission_for_verification',
            message_key='vehicle_submitted',
            event_id=str(vehicle.id)
        )
        
        # Notification pour l'ADMIN (si backoffice_admin existe)
        if backoffice_admin:
            send_notification_with_push(
                sender=driver,
                recipient=backoffice_admin,
                notification_type='vehicle_submission_for_verification',
                message_key='vehicle_submitted_admin',
                event_id=str(vehicle.id)
            )
        
        return Response({
            "Message": "Vehicle was created successfully",
            "vehicle_id": str(vehicle.id),
            "validation_status": vehicle.validation_status
        }, status=status.HTTP_200_OK)
    
    return Response({"Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    
    


@extend_schema(
   tags=['KYC Drivers'], 
   responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_validation_status_Kyc_driver_vehicle(request: Request):
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        vehicle = Vehicle.objects.get(driver_id=users.id)
        return Response({
            "Message": "Validation status KYC driver vehicle",
            "Data": vehicle.validation_status
        }, status=status.HTTP_200_OK)
    except Vehicle.DoesNotExist:
        return Response({
            "Message": "Vehicle not found for the given driver"
        }, status=status.HTTP_200_OK)
      
        
        
    
@extend_schema(
    tags=['Drivers'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])

@permission_classes([IsAuthenticated])
def get_stats_drivers(request:Request , *args, **kwargs) : 
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    try : 
        
        drivers = Drivers.objects.get(id = users.id)
        rides = Rides.objects.filter(driver_id =drivers )
        total_rides_counts = rides.count() or 0 
        
        average_rating   = ReviewRating.objects.filter(driver_id =drivers ).aggregate(Avg('rating'))['rating__avg'] or 0 
        total_spent      = Rides.objects.filter(driver_id =drivers ).aggregate(Sum('final_price'))['final_price__sum'] or 0 

        
        content = {"Message":"Drivers Stats" , 
                   "Data" : {'drivers_id':drivers.id,
                   'total_rides':total_rides_counts,  
                   'total_spent' : total_spent , 
                   'average_rating' :  round(average_rating,2)  }
                   }
        
        
        return Response(data=content , status=status.HTTP_200_OK)
        
    except Drivers.DoesNotExist : 
        content = {"Message":"Drivers Does Not Exist"}
        return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
    
@extend_schema(
    tags=['Grades'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_drivers_grades(request:Request , *args, **kwargs) : 
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    driver_grades = DriverGrade(driver_id=users.id)
    all_information , _ = driver_grades.get_grade_for_a_driver()
    content = {"Message": "Driver Grade", "Data":all_information}
    return Response(data=content, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Grades'], 
    summary="Obtenir la progression vers le prochain grade",
    description="""
    Cet endpoint permet à un chauffeur de suivre sa progression vers le prochain grade.
    Il fournit des informations détaillées sur les exigences à remplir pour atteindre le grade supérieur.
    
    Retourne :
    - Le grade actuel du chauffeur
    - Le prochain grade à atteindre (si applicable)
    - La progression globale en pourcentage
    - Les exigences détaillées pour chaque critère
    """,
    responses={
        200: {
            'description': 'Progression récupérée avec succès',
            'content': {
                'application/json': {
                    'example': {
                        "Current Position": {
                            "percentage_to_next_grade": 60,
                            "Data": {
                                "rating": 4.8,
                                "reviews": 200,
                                "referrals_count": 3,
                                "revenue": 766400.0,
                                "total_count_rides": True,
                                "grade": "Bronze"
                            }
                        },
                        "Next Position": {
                            "percentage_remaining_to_next_grade": 40,
                            "grade": "Silver",
                            "Data": {
                                "rating": 4,
                                "reviews": 50,
                                "total_count_rides": 300,
                                "revenue": 2000000,
                                "referrals_count": 2
                            }
                        }
                    }
                }
            }
        },
        404: {'description': 'Chauffeur non trouvé'},
        500: {'description': 'Erreur serveur'}
    }
)


@extend_schema(
    tags=['Grades'],
    summary="Get all grades with their requirements",
    description="Returns all active grades with their commission rates and progression requirements",
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_grades_requirements(request: Request, *args, **kwargs):
    """
    Retourne tous les grades avec leurs critères de progression.
    Permet au chauffeur de voir ce qu'il faut pour atteindre chaque grade.
    """
    from drivers.grades import DriverGrade as DriverGradeHelper
    from drivers.models import Grade
    
    _, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    # Récupérer tous les grades actifs
    active_grades = Grade.objects.filter(is_active=True).order_by('commission_rate')
    
    # Récupérer les seuils depuis la classe DriverGrade
    helper = DriverGradeHelper(driver_id=users.id)
    thresholds = helper.grades_thresholds  # Dictionnaire avec les seuils
    
    grades_data = []
    for grade in active_grades:
        grade_requirements = thresholds.get(grade.name, {})
        
        grades_data.append({
            'id': grade.id,
            'name': grade.name,
            'commission_rate': float(grade.commission_rate),
            'requirements': {
                'rating': grade_requirements.get('rating', 0),
                'reviews': grade_requirements.get('reviews', 0),
                'total_rides': grade_requirements.get('total_count_rides', 0),
                'revenue': grade_requirements.get('revenue', 0),
                'referrals': grade_requirements.get('referrals_count', 0)
            }
        })
    
    return Response({
        "Message": "All grades with requirements",
        "Data": grades_data
    }, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_drivers_grades_evolution(request: Request, *args, **kwargs):
    """
    Récupère la progression du chauffeur vers le prochain grade.
    
    Retourne les informations détaillées sur la progression du chauffeur vers le prochain grade,
    y compris les exigences à remplir et la progression actuelle pour chaque critère.
    """
    try:
        # Récupérer l'utilisateur à partir du token JWT
        _, user = JWT.filter_and_decode_token(request.headers.get("Authorization"))
        
        # Récupérer le chauffeur
        try:
            driver = Drivers.objects.get(id=user.id)
        except Drivers.DoesNotExist:
            return Response(
                {"error": "Chauffeur non trouvé"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Utiliser notre classe DriverGrade pour calculer la progression
        driver_grade = DriverGrade(driver_id=driver.id)
        evolution_data = driver_grade.get_evolution_to_next_grade()
        
        return Response(evolution_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        # En cas d'erreur inattendue, renvoyer une erreur 500
        import traceback
        error_details = str(e)
        traceback.print_exc()  # Log l'erreur complète dans la console
        return Response(
            {"error": f"Erreur lors de la récupération de la progression: {error_details}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@extend_schema(
    tags=['Drivers'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def update_driver_availability(request:Request, *args, **kwargs):
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        driver = Drivers.objects.get(id=users)
        driver.is_available = True
        driver.save()
        return Response({"Message": "Availability successfully updated."}, status=status.HTTP_200_OK)
    except  Drivers.DoesNotExist:
        return Response({"Message": "Driver not found."}, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
    
    
@extend_schema(
    tags=['Drivers'], 
    request=UpdateUserProfile, 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_driver_profile_picture(request):
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        driver = Drivers.objects.get(id=users.id)
    except Drivers.DoesNotExist:
        return Response({"Message": "Driver Not Found"}, status=status.HTTP_404_NOT_FOUND)

    
    user_profile = request.data
    serializer = UpdateUserProfile(data = user_profile)
    
    if serializer.is_valid(): 
        driver.profile_picture = serializer.validated_data['profile_picture']
        driver.save()


        return Response({
            "Message": "Profile picture uploaded successfully", 
            "Profile Picture URL":  request.build_absolute_uri(driver.profile_picture.url) 
        }, status=status.HTTP_200_OK)
        
    return Response({"Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    tags=['Drivers Subscription'],
    request=SubscriptionDepositSeriaizer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_driver(request):
    """
    Endpoint to subscribe a driver.
    """
    _, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    duration_days = 365  

    if Subscription.objects.filter(driver_id=users.id, active=True, end_date__gte=timezone.now()).exists():
        return Response({"Message": "You already have an active subscription."}, status=status.HTTP_400_BAD_REQUEST)

    # Étapes supplémentaires : effectuer le paiement et créer l'abonnement
    # (Remplacez le TODO ci-dessous par une implémentation réelle de paiement)
    # TODO: Intégrer l'API de paiement tiers

    end_date = timezone.now() + timedelta(days=duration_days)
    driver = Drivers.objects.get(id=users.id)
    subscription = Subscription.objects.create(driver_id=driver, end_date=end_date, active=True)

    try:
        # Essayer de redistribuer les gains de parrainage
        print("Transfert Referrals earning started ...")
        ReferralsEarnings().redistribution_of_referrals_earnings_for_driver(driver.id)
        print("Transfert Referrals earning completed ...")
    except ValueError as e:
        # Aucun parrainage trouvé, continuer l'abonnement
        pass
    except PermissionError as e:
        # Le coupon a déjà été utilisé
        return Response({"Message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    user_id = RetrieveBackofficeUser().retrieve_backoffice_user(users.id)
    send_notification_with_push(

        sender=user_id,

        recipient=driver,

        notification_type='subscription_payment',

        message_key='subscription_activated',

        event_id=subscription.id,

    )
    notifications.save()
    
    return Response({
        "Message": "Subscription created successfully",
        "Subscription ID": subscription.id,
        "End Date": subscription.end_date
    }, status=status.HTTP_201_CREATED)



@extend_schema(
    tags=['Drivers Subscription'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription_status(request):
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    try:
        subscription = Subscription.objects.filter(driver_id=users.id, active=True).latest('end_date')
        is_active = subscription.is_active()
        content  = {"Message": "Subscription Information", 
            "Data" :{ 
                "Subscription Active": is_active,
            "End Date": subscription.end_date,
            "Subscription ID": subscription.id
            }
          
        }
        return Response(data=content , status=status.HTTP_200_OK)
    except Subscription.DoesNotExist:
        return Response({"Message": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)



@extend_schema(
    tags=['Drivers Subscription'], 
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    try:
        subscription = Subscription.objects.filter(driver_id=users.id, active=True).latest('end_date')
        subscription.active = False 
        subscription.save()
        return Response({"Message": "Subscription canceled successfully"}, status=status.HTTP_200_OK)
    except Subscription.DoesNotExist:
        return Response({"Message": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    operation_id="retrieve_vehicle_details",
    tags=['KYC Drivers'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid data'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Vehicle not found'}}},
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_vehicle_details(request, *args, **kwargs):
    """
    Retrieve details of a single vehicle for the authenticated driver.
    """
    _ , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        vehicle = Vehicle.objects.filter(driver=users.id).first()
    except Vehicle.DoesNotExist:
        content = {"Message": "Vehicle not found.", "Data": []}
        return Response(data=content, status=status.HTTP_200_OK)

    vehicle_data = {
        "id": vehicle.id,
        "driver_id": vehicle.driver_id,
        "vehicle_brand": vehicle.vehicle_brand,
        "vehicle_model": vehicle.vehicle_model,
        "license_plate": vehicle.license_plate,
        "vehicle_color": vehicle.vehicle_color,
        "prestation": vehicle.prestation,
        "technical_inspection_date": vehicle.technical_inspection_date,
        "photos": request.build_absolute_uri(vehicle.photos.url) if vehicle.photos else None,
        "vehicle_rental_contract": request.build_absolute_uri(vehicle.vehicle_rental_contract.url) if vehicle.vehicle_rental_contract else None,
        "driving_licence_front": request.build_absolute_uri(vehicle.driving_licence_front.url) if vehicle.driving_licence_front else None,
        "driving_licence_back": request.build_absolute_uri(vehicle.driving_licence_back.url) if vehicle.driving_licence_back else None,
        "insurrance_file": request.build_absolute_uri(vehicle.insurrance_file.url) if vehicle.insurrance_file else None,
        "validation_status": vehicle.validation_status,
        "uploaded_at": vehicle.uploaded_at,
    }

    content = {"Message": "Vehicle details retrieved successfully", "Data": vehicle_data}
    return Response(data=content, status=status.HTTP_200_OK)












@extend_schema(
    tags=['KYC Drivers'],
    request=VehicleDriverSerializer,
    responses={200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}}
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_Kyc_driver_vehicle(request: Request):
    """
    Update the KYC details for a driver's vehicle.

    This endpoint allows an authenticated driver to update their vehicle's KYC details.
    It requires the vehicle ID and the updated details in the request body.

    Parameters:
    - request: The HTTP request containing the updated vehicle data.
    - vehicle_id: The ID of the vehicle to be updated.

    Returns:
    - Response: A message indicating success or failure of the update operation.
    """
    _, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    vehicle_data = request.data

    try:
        vehicle = Vehicle.objects.filter(driver_id=users.id).first()
    except Vehicle.DoesNotExist:
        return Response({"Message": "Vehicle not found or not owned by the user."}, status=status.HTTP_404_NOT_FOUND)

    serializer = VehicleDriverSerializer(vehicle, data=vehicle_data, partial=True)
    if serializer.is_valid():
        data = serializer.save()

        return Response({"Message": "Vehicle was updated successfully"}, status=status.HTTP_200_OK)

    return Response({"Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Drivers'],
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
    Rate limited to 5 requests per hour per phone number (configurable in core/throttling.py).
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
        user = Drivers.objects.get(phone_number=phone_number)
    except Drivers.DoesNotExist:
        return Response({"Message": "User not found. Please register first."}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if already verified
    if user.is_phone_verified:
        return Response({"Message": "Phone number already verified."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate and send OTP
    otp = SignupOTPManager.generate_signup_otp(user)
    message = f"Votre code de validation TOYA est : {otp}. Valide 15 minutes."
    
    # Send via Celery task
    notifiy_new_user_with_sms_tasks.delay(str(user.phone_number), message)
    
    return Response({"Message": "OTP sent successfully to your phone.", "OTP": otp}, status=status.HTTP_200_OK) 


@extend_schema(
    tags=['Drivers'],
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
    Rate limited to 10 requests per hour per phone number (configurable in core/throttling.py).
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
        user = Drivers.objects.get(phone_number=phone_number)
    except Drivers.DoesNotExist:
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
    tags=['Drivers - Development'],
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string'}}},
        403: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_driver_account(request: Request) -> Response:
    """
    **DEVELOPMENT ONLY**: Reset driver account to initial state.
    Clears all related data (rides, payments, vehicles, etc.) but keeps the account.
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
        driver = Drivers.objects.get(id=users.id)
        
        # Import all related models
        from rides.models import Rides, ReviewRating
        from payments.models import PaymentsDrivers, PaymentPhoneNumber
        from support.models import SupportTicket, SupportsConversation
        from conversation.models import Conversation
        from notifications.models import Notifications
        from referrals.models import ReferralsDrivers
        from drivers.models import Vehicle, Subscription
        from core.models import PasswordResetCode, SignupOTP
        
        # Clear all related data
        Rides.objects.filter(driver_id=driver).delete()
        ReviewRating.objects.filter(driver_id=driver).delete()
        PaymentsDrivers.objects.filter(driver_id=driver).delete()
        PaymentPhoneNumber.objects.filter(driver=driver).delete()
        SupportTicket.objects.filter(users_id=driver).delete()
        SupportsConversation.objects.filter(sender_id=driver).delete()
        SupportsConversation.objects.filter(receiver_id=driver).delete()
        Conversation.objects.filter(sender_id=driver).delete()
        Conversation.objects.filter(receiver_id=driver).delete()
        Notifications.objects.filter(sender=driver).delete()
        Notifications.objects.filter(recipient=driver).delete()
        ReferralsDrivers.objects.filter(referrer_driver_id=driver).delete()
        ReferralsDrivers.objects.filter(referred_driver_id=driver).delete()
        Vehicle.objects.filter(driver_id=driver).delete()
        Subscription.objects.filter(driver_id=driver).delete()
        PasswordResetCode.objects.filter(user=driver).delete()
        SignupOTP.objects.filter(user=driver).delete()
        
        # Reset account flags and wallet
        driver.is_phone_verified = False
        driver.wallet_money = 0
        driver.is_available = False
        driver.save()
        
        return Response(
            {
                "Message": "Driver account reset successfully. All related data cleared.",
                "Details": {
                    "phone_verified": False,
                    "wallet_balance": 0,
                    "is_available": False,
                    "account_status": "reset"
                }
            },
            status=status.HTTP_200_OK
        )
        
    except Drivers.DoesNotExist:
        return Response(
            {"Message": "Driver not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"Message": f"Error resetting account: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Drivers - Development'],
    request={
        'application/json': {
            'properties': {
                'amount': {'type': 'integer', 'example': 5000, 'description': 'Amount to set wallet balance to'}
            },
            'required': ['amount']
        }
    },
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string'}, 'new_balance': {'type': 'integer'}}},
        403: {'type': 'object', 'properties': {'Message': {'type': 'string'}}}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def adjust_driver_wallet(request: Request) -> Response:
    """
    **DEVELOPMENT ONLY**: Adjust driver wallet balance for testing.
    Allows setting wallet to any amount to test payment flows.
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
        driver = Drivers.objects.get(id=users.id)
        
        amount = request.data.get('amount')
        
        if amount is None:
            return Response(
                {"Message": "Amount is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return Response(
                {"Message": "Amount must be a valid integer."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_balance = driver.wallet_money
        driver.wallet_money = amount
        driver.save()
        
        return Response(
            {
                "Message": "Wallet balance adjusted successfully.",
                "old_balance": old_balance,
                "new_balance": driver.wallet_money
            },
            status=status.HTTP_200_OK
        )
        
    except Drivers.DoesNotExist:
        return Response(
            {"Message": "Driver not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"Message": f"Error adjusting wallet: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
