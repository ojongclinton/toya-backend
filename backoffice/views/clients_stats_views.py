
from clients.models import Clients
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from rides.models import Rides  , ReviewRating
from drf_spectacular.utils import extend_schema
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.db.models import Q
from payments.models import PaymentsClients
from referrals.models import ReferralsClient
from django.db.models import F, Sum, Count, Avg, ExpressionWrapper, DurationField
from django.db.models.functions import TruncMonth
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated
from calendar import monthrange
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncDay
from django.db.models import Sum, F, ExpressionWrapper, DurationField
import calendar





@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clients_daily_ride_count_statistics(request, client_id:str):
    """
    Retrieve daily statistics for the count of completed rides, including zero for missing days.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    now = timezone.now()
    current_year = now.year
    current_month = now.month

    num_days = monthrange(current_year, current_month)[1]  
    all_days = [
        (datetime(current_year, current_month, day)).strftime('%Y-%m-%d')
        for day in range(1, num_days + 1)
    ]

    ride_count_data = (
        Rides.objects.filter(
            client_id = client_id, 
            accepted_time__year=current_year,
            accepted_time__month=current_month,
            status="completed"
        )
        .annotate(day=TruncDay('accepted_time'))
        .values('day', 'prestation')
        .annotate(total_rides=Count('id'))
        .order_by('day', 'prestation')
    )

    statistics = {day: {} for day in all_days}

    for ride in ride_count_data:
        day = ride['day'].strftime('%Y-%m-%d')
        prestation = ride['prestation']
        total_rides = ride['total_rides']

        if prestation not in statistics[day]:
            statistics[day][prestation] = 0
        statistics[day][prestation] += total_rides

    for day in statistics:
        prestations_for_day = statistics[day]
        for prestation in set([ride['prestation'] for ride in ride_count_data]):
            if prestation not in prestations_for_day:
                prestations_for_day[prestation] = 0

    return Response({
        "Message": "Daily ride count statistics by prestation (completed rides only)",
        "Data": statistics
    } , status = status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clients_monthly_ride_count_statistics(request , client_id :str):
    """
    Retrieve monthly statistics for the count of completed rides, including zero for months with no data.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year

    ride_count_data = (
        Rides.objects.filter(
            client_id = client_id,  
            accepted_time__year=current_year,
            status="completed"
        )
        .annotate(month=TruncMonth('accepted_time'))
        .values('month', 'prestation')
        .annotate(total_rides=Count('id'))
        .order_by('month', 'prestation')
    )

    all_months = {f"{current_year}-{month:02d}": {} for month in range(1, 13)}

    for ride in ride_count_data:
        month = ride['month'].strftime('%Y-%m')
        prestation = ride['prestation']
        total_rides = ride['total_rides']

        if prestation not in all_months[month]:
            all_months[month][prestation] = 0
        all_months[month][prestation] += total_rides

    for month in all_months:
        prestations_for_month = all_months[month]
        for prestation in set([ride['prestation'] for ride in ride_count_data]):
            if prestation not in prestations_for_month:
                prestations_for_month[prestation] = 0

    return Response({
        "Message": "Monthly ride count statistics by prestation (completed rides only)",
        "Data": all_months
    } ,  status = status.HTTP_200_OK)







@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'clients not found'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clients_revenue_by_month_and_year(request, client_id):
    """
    Retrieve monthly and yearly revenue for a specific clients.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    year = int(request.GET.get("year", datetime.now().year))

    try:
        client = Clients.objects.get(id=client_id)
    except Clients.DoesNotExist:
        return Response({
            "Message": "clients not found"
        }, status=status.HTTP_404_NOT_FOUND)

    monthly_revenue = (
        PaymentsClients.objects.filter(
            client_id=client,
            payments_status='completed',
            created_at__year=year  
        )
        .annotate(month=TruncMonth('created_at'))  
        .values('month')
        .annotate(total_revenue=Sum('amount')) 
        .order_by('month') 
    )

    monthly_data = {
        f"{year}-{str(month).zfill(2)}": 0 for month in range(1, 13)
    }

    for revenue in monthly_revenue:
        month_str = revenue['month'].strftime('%Y-%m')  
        monthly_data[month_str] = round(revenue['total_revenue'] or 0, 2)

    response_data = {
        'client_Id': client.id,
        'monthly_revenue': monthly_data,
        'total_revenue': sum(monthly_data.values()),
    }

    return Response({
        "Message": "clients Revenue by Month and Year",
        "Data": response_data
    }, status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'clients not found'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clients_daily_revenue_by_month(request, client_id: str):
    """
    Retrieve daily expenses for a specific client within a given month, including zero for missing days.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    now = timezone.now()
    year = int(request.GET.get("year", now.year))
    month = int(request.GET.get("month", now.month))

    num_days = monthrange(year, month)[1]
    all_days = [
        datetime(year, month, day).strftime('%Y-%m-%d') for day in range(1, num_days + 1)
    ]

    try:
        client = Clients.objects.get(id=client_id)
    except Clients.DoesNotExist:
        return Response({
            "Message": "Client not found"
        }, status=status.HTTP_404_NOT_FOUND)

    daily_expenses_data = (
        PaymentsClients.objects.filter(
            client_id=client,
            payments_status='completed',
            created_at__year=year,
            created_at__month=month
        )
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total_expenses=Sum('amount'))
        .order_by('day')
    )

    daily_expenses = {day: 0 for day in all_days}

    for expense in daily_expenses_data:
        day = expense['day'].strftime('%Y-%m-%d')
        daily_expenses[day] = round(expense['total_expenses'] or 0, 2)

    response_data = {
        'client_id': client.id,
        'daily_expenses': daily_expenses,
        'total_expenses': sum(daily_expenses.values()), 
    }

    return Response({
        "Message": "Client Daily Expenses for the Month",
        "Data": response_data
    }, status=status.HTTP_200_OK)






@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'clients not found'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_referrals_by_day(request, client_id: str):
    """
    Retrieve daily referral statistics for a specific client in a given month.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    now = timezone.now()
    year = int(request.GET.get("year", now.year))
    month = int(request.GET.get("month", now.month))

    num_days = monthrange(year, month)[1]
    all_days = [
        datetime(year, month, day).strftime('%Y-%m-%d') for day in range(1, num_days + 1)
    ]

    try:
        client = Clients.objects.get(id=client_id)
    except Clients.DoesNotExist:
        return Response({
            "Message": "Client not found"
        }, status=status.HTTP_404_NOT_FOUND)

    daily_referrals_data = (
        ReferralsClient.objects.filter(
            referrer_client_id=client,
            created_at__year=year,
            created_at__month=month
        )
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total_referrals=Count('id'))
        .order_by('day')
    )

    daily_referrals = {day: 0 for day in all_days}

    for referral in daily_referrals_data:
        day = referral['day'].strftime('%Y-%m-%d')
        daily_referrals[day] = referral['total_referrals']

    response_data = {
        'client_id': client.id,
        'daily_referrals': daily_referrals,
        'total_referrals': sum(daily_referrals.values()), 
    }

    return Response({
        "Message": "Client Daily Referrals for the Month",
        "Data": response_data
    }, status=status.HTTP_200_OK)




@extend_schema(
    tags=['BackOffice Clients'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'clients not found'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_referrals_by_month(request, client_id: str):
    """
    Retrieve monthly referral statistics for a specific client in a given year.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    now = timezone.now()
    year = int(request.GET.get("year", now.year))

    try:
        client = Clients.objects.get(id=client_id)
    except Clients.DoesNotExist:
        return Response({
            "Message": "Client not found"
        }, status=status.HTTP_404_NOT_FOUND)

    monthly_referrals_data = (
        ReferralsClient.objects.filter(
            referrer_client_id=client,
            created_at__year=year
        )
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total_referrals=Count('id'))
        .order_by('month')
    )

    monthly_referrals = {
        f"{year}-{str(month).zfill(2)}": 0 for month in range(1, 13)
    }

    for referral in monthly_referrals_data:
        month_str = referral['month'].strftime('%Y-%m')
        monthly_referrals[month_str] = referral['total_referrals']

    response_data = {
        'client_id': client.id,
        'monthly_referrals': monthly_referrals,
        'total_referrals': sum(monthly_referrals.values()),  
    }

    return Response({
        "Message": "Client Monthly Referrals for the Year",
        "Data": response_data
    }, status=status.HTTP_200_OK)
