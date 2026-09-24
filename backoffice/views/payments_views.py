from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view , permission_classes
from payments.models import PaymentsDrivers, PaymentsClients
from ..serializers import *
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from django.db.models import Sum , Avg
from datetime import datetime, timedelta
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated


@extend_schema(
    tags=['BackOffice Payment'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET']) 
@permission_classes([IsAuthenticated])
def get_all_payments_client(request):
    """
    Retrieve a list of all payments.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    client_payments = PaymentsClients.objects.all()
    client_serializer = PaymentsClientsSerializer(client_payments, many=True)
    
    content = {"Message": "list of all payments client", "Data":{ 'client_payments': client_serializer.data,
        }
    }
    return Response(data=content, status=status.HTTP_200_OK)


@extend_schema(
    tags=['BackOffice Payment'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET']) 
@permission_classes([IsAuthenticated])
def get_all_payments_drivers(request):
    """
    Retrieve a list of all payments.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    driver_payments = PaymentsDrivers.objects.all()
    driver_serializer = PaymentsDriversSerializer(driver_payments, many=True)
    
    content = {"Message": "list of all payments drivers", "Data":{ 
        'drivers_payments': driver_serializer.data
        }
    }
    return Response(data=content, status=status.HTTP_200_OK)





@extend_schema(
    tags=['BackOffice Payment'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_detail_drivers(request, payment_id):
    """
    Retrieve the details of a specific payment.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        payment = PaymentsDrivers.objects.get(id=payment_id)
        serializer =  PaymentsDriversSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except PaymentsClients.DoesNotExist:
        return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)








@extend_schema(
    tags=['BackOffice Payment'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_detail_client(request, payment_id):
    """
    Retrieve the details of a specific payment.
    """
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    try:
        payment = PaymentsClients.objects.get(id=payment_id) 
        serializer = PaymentsClientsSerializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except PaymentsClients.DoesNotExist:
        return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)



@extend_schema(
    tags=['BackOffice Payment'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_payments(request):
    """
    Retrieve all payments made with 'wallet_pay' type."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    wallet_payments = PaymentsDrivers.objects.filter(payments_type="wallet_pay")
    serializer = PaymentsDriversSerializer(wallet_payments, many=True)
    content = {"Message":"all payments made with wallet_pay type." , "Data":serializer.data,}
    return Response(data=content,  status=status.HTTP_200_OK)




@extend_schema(
    tags=['BackOffice Payment'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET']) 
@permission_classes([IsAuthenticated])
def get_wallet_payment_statistics(request):
    """
    Retrieve statistics of 'wallet_pay' payments for the current month, week, and year."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    today = timezone.now()  

    start_of_month = today.replace(day=1)
    start_of_week = today - timezone.timedelta(days=today.weekday())
    start_of_year = today.replace(month=1, day=1)

    monthly_earnings = PaymentsDrivers.objects.filter(
        payments_type="wallet_pay", created_at__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    weekly_earnings = PaymentsDrivers.objects.filter(
        payments_type="wallet_pay", created_at__gte=start_of_week
    ).aggregate(total=Sum('amount'))['total'] or 0

    yearly_earnings = PaymentsDrivers.objects.filter(
        payments_type="wallet_pay", created_at__gte=start_of_year
    ).aggregate(total=Sum('amount'))['total'] or 0

    content = {"Message":" statistics of 'wallet_pay' payments for the current month, week, and year", "Data":{
        "monthly_earnings": monthly_earnings,
        "weekly_earnings": weekly_earnings,
        "yearly_earnings": yearly_earnings
    }}
    
    return Response(data=content, status=status.HTTP_200_OK)




@extend_schema(
    tags=['BackOffice Payment'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET']) 
@permission_classes([IsAuthenticated])
def payment_statistics(request):
    """Retrieve payment statistics for clients and drivers on a daily, weekly, and monthly basis for charting."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    today = datetime.now().date()
    last_30_days = [today - timedelta(days=i) for i in range(30)]
    
    daily_data_clients = {
        'dates': [],
        'total_payments': [],
        'total_amount': []
    }
    daily_data_drivers = {
        'dates': [],
        'total_payments': [],
        'total_amount': []
    }
    
    for single_date in last_30_days:
        daily_client_payments = PaymentsClients.objects.filter(created_at__date=single_date)
        daily_driver_payments = PaymentsDrivers.objects.filter(created_at__date=single_date)
        
        daily_data_clients['dates'].append(single_date.strftime('%Y-%m-%d'))
        daily_data_clients['total_payments'].append(daily_client_payments.count())
        daily_data_clients['total_amount'].append(daily_client_payments.aggregate(total=Sum('amount'))['total'] or 0)
        
        daily_data_drivers['dates'].append(single_date.strftime('%Y-%m-%d'))
        daily_data_drivers['total_payments'].append(daily_driver_payments.count())
        daily_data_drivers['total_amount'].append(daily_driver_payments.aggregate(total=Sum('amount'))['total'] or 0)
    
    weekly_data_clients = {
        'week_start_dates': [],
        'total_payments': [],
        'total_amount': []
    }
    weekly_data_drivers = {
        'week_start_dates': [],
        'total_payments': [],
        'total_amount': []
    }
    
    for week in range(4):
        week_start = today - timedelta(weeks=week + 1)
        weekly_client_payments = PaymentsClients.objects.filter(created_at__date__gte=week_start, created_at__date__lt=week_start + timedelta(weeks=1))
        weekly_driver_payments = PaymentsDrivers.objects.filter(created_at__date__gte=week_start, created_at__date__lt=week_start + timedelta(weeks=1))
        
        weekly_data_clients['week_start_dates'].append(week_start.strftime('%Y-%m-%d'))
        weekly_data_clients['total_payments'].append(weekly_client_payments.count())
        weekly_data_clients['total_amount'].append(weekly_client_payments.aggregate(total=Sum('amount'))['total'] or 0)
        
        weekly_data_drivers['week_start_dates'].append(week_start.strftime('%Y-%m-%d'))
        weekly_data_drivers['total_payments'].append(weekly_driver_payments.count())
        weekly_data_drivers['total_amount'].append(weekly_driver_payments.aggregate(total=Sum('amount'))['total'] or 0)
    
    monthly_data_clients = {
        'month_names': [],
        'total_payments': [],
        'total_amount': []
    }
    monthly_data_drivers = {
        'month_names': [],
        'total_payments': [],
        'total_amount': []
    }
    
    for month in range(1, 13):
        month_start = today.replace(day=1, month=month) if month <= today.month else today.replace(day=1, month=month - 1)
        
        monthly_client_payments = PaymentsClients.objects.filter(created_at__month=month, created_at__year=today.year)
        monthly_driver_payments = PaymentsDrivers.objects.filter(created_at__month=month, created_at__year=today.year)
        
        monthly_data_clients['month_names'].append(month_start.strftime('%B'))
        monthly_data_clients['total_payments'].append(monthly_client_payments.count())
        monthly_data_clients['total_amount'].append(monthly_client_payments.aggregate(total=Sum('amount'))['total'] or 0)
        
        monthly_data_drivers['month_names'].append(month_start.strftime('%B'))
        monthly_data_drivers['total_payments'].append(monthly_driver_payments.count())
        monthly_data_drivers['total_amount'].append(monthly_driver_payments.aggregate(total=Sum('amount'))['total'] or 0)
    
    
    monthly_data_clients['month_names'][-1] = "December"
    monthly_data_drivers['month_names'][-1] = "December"

    
    response_data = {
        'client_payment_stats': {
            'daily_stats': daily_data_clients,
            'weekly_stats': weekly_data_clients,
            'monthly_stats': monthly_data_clients
        },
        'driver_payment_stats': {
            'daily_stats': daily_data_drivers,
            'weekly_stats': weekly_data_drivers,
            'monthly_stats': monthly_data_drivers
        }
    }
    
    content = {"Message": "Payment Statistics", "Data": response_data}
    return Response(data=content, status=status.HTTP_200_OK)
