from rest_framework import status 
from rest_framework.response import Response 
from rest_framework.request import Request 
from rest_framework.decorators import api_view , permission_classes 
from drivers.models import Drivers , Vehicle
import re
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from ..customs import JWT
from rides.models import Rides
from django.db.models import Count , Sum
from payments.models import PaymentsDrivers
from datetime import timedelta
from django.db.models import Sum, Count, F, ExpressionWrapper, DurationField
from notifications.models import Notifications
from ..models import BackofficeAdmin
from datetime import datetime
from django.utils import timezone
from core.utils.translations import get_message
from core.utils.language import get_user_language

@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_all_drivers(request:Request , *args, **kwargs) : 
    """
    Récupère tous les clients avec leurs détails, 
    y compris le nombre de courses et le total dépensé.
    """
    try:
        token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
        
        drivers = Drivers.objects.values(
            "id", "username", "email", "first_name", "last_name", 
            "phone_number", "adresse", "date_joined", "referral_code"
        )
        
        driver_data = []
        for driver in drivers:
            driver_id = driver["id"]
            
            rides_info = Rides.objects.filter(driver_id=driver_id , status ='completed' ).aggregate(
                total_spent=Sum("final_price"), 
                total_rides=Count("id"), 
                total_duration=Sum(
                ExpressionWrapper(F('end_time') - F('start_time'), output_field=DurationField())
            )
            )
            
            driver["total_rides"] = rides_info["total_rides"] or 0
            driver["total_spent"] = rides_info["total_spent"] or 0.0
            driver["total_duration_hours"]  =  rides_info["total_duration"]  or timedelta(seconds=0)
            driver_data.append(driver)

        content = {"Message": "All customers successfully recovered", "Data": driver_data}
        return Response(data=content, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            data={"Message": f"Error retrieving customers : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )





@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retrieve_details_of_drivers(request: Request, drivers_id: str, *args, **kwargs): 
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        drivers = Drivers.objects.get(id=drivers_id)
        print(drivers.id, drivers.first_name)

        rides_info = Rides.objects.filter(driver_id=drivers.id, status='completed').aggregate(
            total_spent=Sum("final_price"),
            total_rides=Count("id"),
            total_duration=Sum(
                ExpressionWrapper(F('end_time') - F('start_time'), output_field=DurationField())
            )
        )

        total_rides = rides_info["total_rides"] or 0
        total_spent = rides_info["total_spent"] or 0.0
        total_duration = rides_info["total_duration"] or timedelta(seconds=0)
        total_duration_hours = total_duration.total_seconds() / 3600

        try:
            vehicle = Vehicle.objects.get(driver_id=drivers.id)
            vehicle_data = {
                'vehicle_model': vehicle.vehicle_model,
                'license_plate': vehicle.license_plate,
                'prestation': vehicle.prestation,
                'technical_inspection_date': vehicle.technical_inspection_date,
                'validation_status': vehicle.validation_status,
                'uploaded_at': vehicle.uploaded_at,
            }
        except Vehicle.DoesNotExist:
            vehicle_data = {
                'vehicle_model': "Not specified",
                'license_plate': "Not specified",
                'prestation': None,
                'technical_inspection_date': None,
                'validation_status': None,
                'uploaded_at': None,
            }

        data = {
            'id': drivers.id,
            'username': drivers.id,
            'email': drivers.email,
            'first_name': drivers.first_name,
            'last_name': drivers.last_name,
            'phone_number': drivers.phone_number,
            'adresse': drivers.adresse,
            "date_joined": drivers.date_joined,
            "referral_code": drivers.referral_code,
            'total_rides': total_rides,
            'total_spent': total_spent,
            'total_duration_hours': round(total_duration_hours, 2),
            **vehicle_data 
        }

    except Drivers.DoesNotExist:
        content = {"Message": "User does not exist"}
        return Response(data=content, status=status.HTTP_404_NOT_FOUND)

    content = {"Message": 'Driver Details', "Data": data}
    return Response(data=content, status=status.HTTP_200_OK)



    
@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_drivers_account(request:Request , drivers_id :str , *args, **kwargs) : 
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        
        drivers = Drivers.objects.get(id = drivers_id)
        drivers.delete()
        
    except Exception as e : 
        content  = {"Message":"User does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    content = {"Message":'Customer account deleted'}
    return Response(data=content , status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Clients'], 
    request={
            'application/json': {
                'properties': {
                    'username': {'type': 'string', 'example': 'username'},
                    'first_name': {'type': 'string', 'example': 'first_name'}, 
                    'last_name': {'type': 'string', 'example': 'last_name'},
                    'phone_number': {'type': 'string', 'example': 'phone_number'},
                    'adresse': {'type': 'string', 'example': 'adresse'},
                }
            }
    }, 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_drivers_account(request:Request ,drivers_id :str,  *args, **kwargs) : 

    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try : 
        drivers = Drivers.objects.get(id = drivers_id)
    except Drivers.DoesNotExist : 
        content  = {"Message":"User does not exist"}
        return Response(data = content , status = status.HTTP_404_NOT_FOUND)
    
    username = request.data.get('username', None)
    first_name = request.data.get('first_name',None)
    last_name = request.data.get('last_name',None)
    phone_number = request.data.get('phone_number',None)
    adresse = request.data.get('adresse',None)
    
    if username:
        drivers.username = username
    if first_name:
        drivers.first_name = first_name
    if last_name:
        drivers.last_name = last_name
    if phone_number:
        
        pattern = r"^\+2376\d{8}$"
    
        if not re.match(pattern, phone_number) : 
            content = {"Message": "Invalid phone number. It should start with +2376 and be followed by 9 digits."}
            return Response(data = content , status = status.HTTP_400_BAD_REQUEST)
        
        drivers.phone_number = phone_number
        
    if adresse:
        drivers.adresse = adresse
        
    drivers.save()

    
    content = {"Message": "User Updated Successfully",}
    return Response(data = content , status = status.HTTP_200_OK)






@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def approve_vehicle_verification(request:Request, driver_id:str):
    """Approve a vehicle's verification status."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        driver = Drivers.objects.get(id = driver_id)
    except Drivers.DoesNotExist : 
        content = {"Message":"Drivers Does Not Exist"}
        return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
    vehicle = Vehicle.objects.get(driver_id = driver.id)
    
    if vehicle: 
        vehicle.validation_status = 'validated'
        vehicle.save()
        
        backoffice = BackofficeAdmin.objects.get(id = users.id)
        notifications = Notifications.objects.create( 
                                                 sender = backoffice, 
                                                 recipient = driver , 
                                                 notification_type='documents_approved',
                                                message=get_message("documents_approved", get_user_language),
                                                event_id=''
                                                 )
        notifications.save()
    
    return Response({"Message": "Vehicle has been approved"}, status=status.HTTP_200_OK)
    
        
    
    

@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_of_approved_vehicles(request):
    
    """List all vehicles that have been approved."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    vehicles = Vehicle.objects.filter(validation_status = "validated" )
    vehicles_data = [{
        "id": vehicle.id, 
        "driver_id": vehicle.driver_id.id,
        "model": vehicle.vehicle_model, 
        "registration_number": vehicle.license_plate,
        "prestation": vehicle.prestation,
        "validation_status": vehicle.validation_status,
        "uploaded_at": vehicle.uploaded_at
    } for vehicle in vehicles]

    content = {"Message": "list of vehicles to approve." , "Data":vehicles_data}
    return Response(data=content, status=status.HTTP_200_OK)
    
         
    
    
@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_of_rejected_vehicles(request):
    """List all vehicles that have been rejected."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    vehicles = Vehicle.objects.filter(validation_status = "rejected" )
    vehicles_data = [{
        "id": vehicle.id, 
        "driver_id": vehicle.driver_id.id,
        "model": vehicle.vehicle_model, 
        "registration_number": vehicle.license_plate,
        "prestation": vehicle.prestation,
        "validation_status": vehicle.validation_status,
        "uploaded_at": vehicle.uploaded_at
    } for vehicle in vehicles]

    content = {"Message": "list of rejected vehicles" , "Data":vehicles_data}
    return Response(data=content, status=status.HTTP_200_OK)
    
    



@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reject_vehicle_verification(request:Request, driver_id:str):
    """Reject a vehicle's verification status."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try : 
        driver = Drivers.objects.get(id = driver_id)
    except Drivers.DoesNotExist : 
        content = {"Message":"Drivers Does Not Exist"}
        return Response(data=content , status=status.HTTP_400_BAD_REQUEST)
    vehicle = Vehicle.objects.get(driver_id = driver.id)
    
    if vehicle: 
        vehicle.validation_status = 'rejected'
        vehicle.save()
        
        backoffice = BackofficeAdmin.objects.get(id=users.id)

        notifications = Notifications.objects.create(
            sender=backoffice,
            recipient=driver,
            notification_type='documents_rejected',
            message=get_message("documents_rejected", get_user_language),
            event_id=''
        )
        notifications.save()
        
        # @ TODO add decision 
    
    return Response({"Message": "Vehicle has been rejected.."}, status=status.HTTP_200_OK)
    
        

    
    
    



@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_of_pending_vehicles(request):
    """    List all vehicles with a pending validation status."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    vehicles = Vehicle.objects.filter(validation_status = "in pending" )
        
    vehicles_data = [{
        "id": vehicle.id, 
        "driver_id": vehicle.driver_id.id,
        "model": vehicle.vehicle_model, 
        "registration_number": vehicle.license_plate,
        "prestation": vehicle.prestation,
        "validation_status": vehicle.validation_status,
        "uploaded_at": vehicle.uploaded_at
    } for vehicle in vehicles]

        
    content = {"Message": "list of pending vehicles" , "Data":vehicles_data}
    return Response(data=content, status=status.HTTP_200_OK)
    
    
    
    
    
@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_vehicle_submission(request: Request, driver_id: str):
    """Retrieves and displays information from the file submitted by a driver for a vehicle."""
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        vehicle = Vehicle.objects.get(driver_id=driver_id)
        
        vehicle_data = {
            "vehicle_model": vehicle.vehicle_model,
            "license_plate": vehicle.license_plate,
            "prestation": vehicle.prestation,
            "full_name": f"{vehicle.driver_id.first_name} {vehicle.driver_id.last_name}", 
            "phone_number": vehicle.driver_id.phone_number, 
            "technical_inspection_date": vehicle.technical_inspection_date,
            "photos_url": request.build_absolute_uri(vehicle.photos.url) if vehicle.photos else None,
            "vehicle_rental_contract_url": request.build_absolute_uri(vehicle.vehicle_rental_contract.url) if vehicle.vehicle_rental_contract else None,
            "driving_licence_front_url": request.build_absolute_uri(vehicle.driving_licence_front.url) if vehicle.driving_licence_front else None,
            "driving_licence_back_url": request.build_absolute_uri(vehicle.driving_licence_back.url) if vehicle.driving_licence_back else None,
            "insurance_file_url": request.build_absolute_uri(vehicle.insurrance_file.url) if vehicle.insurrance_file else None,
            "criminal_record_certificate_url": request.build_absolute_uri(vehicle.criminal_record_certificate.url) if vehicle.criminal_record_certificate else None,
            "technical_control_document_url": request.build_absolute_uri(vehicle.technical_control_document.url) if vehicle.technical_control_document else None,
            "validation_status": vehicle.validation_status,
            "uploaded_at": vehicle.uploaded_at
        }
            
        return Response(vehicle_data, status=status.HTTP_200_OK)

    except Vehicle.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)
    
    
    


@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def drivers_revenue(request):
    """
    Retrieve a list of all drivers with their total earnings from rides.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    drivers = Drivers.objects.all()

    driver_revenue_data = []

    for driver in drivers:
        total_earnings = PaymentsDrivers.objects.filter(
            driver_id=driver,  
            payments_type='ride_payment' 
        ).aggregate(total=Sum('amount'))['total'] or 0

        driver_revenue_data.append({
            'driver_id': driver.id,
            'driver_name': f"{driver.first_name} {driver.last_name}",
            'total_earnings': total_earnings,
        })

    return Response({
        "Message": "Drivers Revenue",
        "Data": driver_revenue_data
    }, status=status.HTTP_200_OK)

@extend_schema(
    tags=['Backoffice - Drivers'],
    summary="Valider un document de véhicule",
    description="""
    Permet à un admin du backoffice de valider un document spécifique d'un véhicule
    et de définir sa date d'expiration.
    
    Types de documents supportés :
    - technical_control : Visite technique
    - insurance : Assurance
    - driving_licence : Permis de conduire  
    - criminal_record : Casier judiciaire
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'document_type': {
                    'type': 'string',
                    'enum': ['technical_control', 'insurance', 'driving_licence', 'criminal_record']
                },
                'expiry_date': {
                    'type': 'string',
                    'format': 'date',
                    'example': '2027-04-01'
                },
                'validation_status': {
                    'type': 'string',
                    'enum': ['validated', 'rejected'],
                    'default': 'validated'
                }
            },
            'required': ['document_type', 'expiry_date']
        }
    },
    responses={
        200: {
            'description': 'Document validé avec succès',
            'content': {
                'application/json': {
                    'example': {
                        'Message': 'Document validé avec succès',
                        'document_type': 'technical_control',
                        'expiry_date': '2027-04-01',
                        'validated_at': '2026-04-02T10:30:00Z'
                    }
                }
            }
        },
        400: {'description': 'Données invalides'},
        404: {'description': 'Véhicule non trouvé'}
    }
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_vehicle_document(request, driver_id):
    """
    Valide un document spécifique d'un véhicule et définit sa date d'expiration.
    """
    from django.utils import timezone
    from datetime import datetime
    
    try:
        # Récupérer le véhicule
        try:
            vehicle = Vehicle.objects.get(driver_id=driver_id)
        except Vehicle.DoesNotExist:
            return Response(
                {"Message": "Véhicule non trouvé pour ce chauffeur"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les données
        document_type = request.data.get('document_type')
        expiry_date_str = request.data.get('expiry_date')
        validation_status = request.data.get('validation_status', 'validated')
        
        # Validation des données
        if not document_type:
            return Response(
                {"Message": "Le type de document est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not expiry_date_str:
            return Response(
                {"Message": "La date d'expiration est requise"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convertir la date
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"Message": "Format de date invalide. Utilisez YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mapper le type de document aux champs du modèle
        document_mapping = {
            'technical_control': {
                'expiry_field': 'technical_control_expiry_date',
                'validated_field': 'technical_control_validated_at'
            },
            'insurance': {
                'expiry_field': 'insurance_expiry_date',
                'validated_field': 'insurance_validated_at'
            },
            'driving_licence': {
                'expiry_field': 'driving_licence_expiry_date',
                'validated_field': 'driving_licence_validated_at'
            },
            'criminal_record': {
                'expiry_field': 'criminal_record_expiry_date',
                'validated_field': 'criminal_record_validated_at'
            }
        }
        
        if document_type not in document_mapping:
            return Response(
                {"Message": f"Type de document invalide. Types valides : {', '.join(document_mapping.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour les champs
        mapping = document_mapping[document_type]
        setattr(vehicle, mapping['expiry_field'], expiry_date)
        
        if validation_status == 'validated':
            setattr(vehicle, mapping['validated_field'], timezone.now())
        
        vehicle.save()
        
        validated_at_value = getattr(vehicle, mapping['validated_field'])
        
        return Response({
            "Message": f"Document {document_type} validé avec succès",
            "document_type": document_type,
            "expiry_date": expiry_date_str,
            "validated_at": validated_at_value.isoformat() if validated_at_value and validation_status == 'validated' else None
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {"Message": f"Erreur lors de la validation: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )