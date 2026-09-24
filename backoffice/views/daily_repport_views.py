
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from rides.models import Rides 
from drf_spectacular.utils import extend_schema
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.db.models import Q

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
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_ride_count_statistics(request):
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
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_ride_count_statistics(request):
    """
    Retrieve monthly statistics for the count of completed rides, including zero for months with no data.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year

    ride_count_data = (
        Rides.objects.filter(
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
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_cancelled_rides_statistics(request):
    """Retrieve daily statistics for the count of cancelled rides."""
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year
    current_month = timezone.now().month

    cancelled_data = (
        Rides.objects.filter(
            accepted_time__year=current_year,
            accepted_time__month=current_month,
            status="cancelled"
        )
        .annotate(day=TruncDay('accepted_time'))
        .values('day')
        .annotate(cancelled_rides=Count('id'))
        .order_by('day')
    )

    days_in_month = range(1, calendar.monthrange(current_year, current_month)[1] + 1)
    statistics = {f"{current_year}-{current_month:02d}-{day:02d}": 0 for day in days_in_month}

    for ride in cancelled_data:
        day = ride['day'].strftime('%Y-%m-%d')
        statistics[day] = ride['cancelled_rides']

    return Response({
        "Message": "Daily cancelled rides statistics",
        "Data": statistics
    } ,  status = status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_cancelled_rides_statistics(request):
    """Retrieve monthly statistics for the count of cancelled rides."""
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year

    cancelled_data = (
        Rides.objects.filter(
            accepted_time__year=current_year,
            status="cancelled"
        )
        .annotate(month=TruncMonth('accepted_time'))
        .values('month')
        .annotate(cancelled_rides=Count('id'))
        .order_by('month')
    )

    all_months = {f"{current_year}-{month:02d}": 0 for month in range(1, 13)}

    for ride in cancelled_data:
        month = ride['month'].strftime('%Y-%m')
        all_months[month] = ride['cancelled_rides']

    return Response({
        "Message": "Monthly cancelled rides statistics",
        "Data": all_months
    } , status = status.HTTP_200_OK)




from django.db.models import F, Sum, DurationField, ExpressionWrapper
from django.db.models.functions import TruncDay, TruncMonth
from datetime import timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.utils import timezone
import calendar
from drf_spectacular.utils import extend_schema

@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_ride_durations(request):
    """Retrieve total ride durations (hours) per day in the current month."""
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year
    current_month = timezone.now().month

    daily_data = (
        Rides.objects.filter(
            accepted_time__year=current_year,
            accepted_time__month=current_month
        )
        .annotate(
            ride_duration=ExpressionWrapper(
                F('end_time') - F('start_time'), 
                output_field=DurationField()
            )
        )
        .filter(ride_duration__gte=timedelta(0))  
        .annotate(day=TruncDay('accepted_time'))
        .values('day')
        .annotate(total_duration=Sum('ride_duration'))
        .order_by('day')
    )

    days_in_month = range(1, calendar.monthrange(current_year, current_month)[1] + 1)
    statistics = {f"{current_year}-{current_month:02d}-{day:02d}": 0 for day in days_in_month}

    for ride in daily_data:
        day = ride['day'].strftime('%Y-%m-%d')
        total_duration_hours = ride['total_duration'].total_seconds() / 3600  
        statistics[day] = round(total_duration_hours, 2)

    return Response({
        "Message": "Daily ride durations in hours",
        "Data": statistics
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_ride_durations(request):
    """Retrieve total ride durations (hours) per month in the current year."""
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year

    monthly_data = (
        Rides.objects.filter(
            accepted_time__year=current_year
        )
        .annotate(
            ride_duration=ExpressionWrapper(
                F('end_time') - F('start_time'),
                output_field=DurationField()
            )
        )
        .filter(ride_duration__gte=timedelta(0))  
        .annotate(month=TruncMonth('accepted_time'))
        .values('month')
        .annotate(total_duration=Sum('ride_duration'))
        .order_by('month')
    )

    all_months = {f"{current_year}-{month:02d}": 0 for month in range(1, 13)}

    for ride in monthly_data:
        month = ride['month'].strftime('%Y-%m')
        total_duration_hours = ride['total_duration'].total_seconds() / 3600  
        all_months[month] = round(total_duration_hours, 2)

    return Response({
        "Message": "Monthly ride durations in hours",
        "Data": all_months
    }, status=status.HTTP_200_OK)
