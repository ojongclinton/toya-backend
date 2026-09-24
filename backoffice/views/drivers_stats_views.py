
from drivers.models import Drivers
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from rides.models import Rides  , ReviewRating
from drf_spectacular.utils import extend_schema
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.db.models import Q
from payments.models import PaymentsDrivers

from django.db.models import F, Sum, Count, Avg, ExpressionWrapper, DurationField
from django.db.models.functions import TruncMonth
from ..customs import JWT
from rest_framework.permissions import IsAuthenticated
from calendar import monthrange
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncDay
from django.db.models import Sum, F, ExpressionWrapper, DurationField
import calendar


    


# @extend_schema(
#     tags=['BackOffice Driver'], 
#     responses={
#             200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
#             400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
#             404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
#     )
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def drivers_revenue(request , driver_id:str):
#     """
#     Retrieve a list of all drivers with their total earnings from rides.
#     """
#     token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

#     drivers = Drivers.objects.all()

#     driver_revenue_data = []

#     for driver in drivers:
#         total_earnings = PaymentsDrivers.objects.filter(
#             driver_id=driver,  
#             payments_type='ride_payment' 
#         ).aggregate(total=Sum('amount'))['total'] or 0

#         driver_revenue_data.append({
#             'driver_id': driver.id,
#             'driver_name': f"{driver.first_name} {driver.last_name}",
#             'total_earnings': total_earnings,
#         })

#     return Response({
#         "Message": "Drivers Revenue",
#         "Data": driver_revenue_data
#     }, status=status.HTTP_200_OK)




@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_daily_ride_count_statistics(request, driver_id:str):
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
            driver_id = driver_id, 
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
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_monthly_ride_count_statistics(request , driver_id:str):
    """
    Retrieve monthly statistics for the count of completed rides, including zero for months with no data.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year

    ride_count_data = (
        Rides.objects.filter(
            driver_id = driver_id, 
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
    tags=['BackOffice Driver'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_daily_ride_durations(request, driver_id:str):
    """Retrieve total ride durations (hours) per day in the current month."""
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year
    current_month = timezone.now().month

    daily_data = (
        Rides.objects.filter(
            driver_id= driver_id, 
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
    tags=['BackOffice Driver'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_monthly_ride_durations(request, driver_id:str):
    """Retrieve total ride durations (hours) per month in the current year."""
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year

    monthly_data = (
        Rides.objects.filter(
            driver_id = driver_id, 
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






@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_average_ratings_daily(request , driver_id:str):
    """Retrieve daily average ratings for drivers and clients."""
    
    year = int(request.GET.get("year", datetime.now().year))
    month = int(request.GET.get("month", datetime.now().month))

    start_date = datetime(year, month, 1)
    next_month = start_date + timedelta(days=31)
    end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
    all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    statistics = {date.strftime('%Y-%m-%d'): {"driver_avg_rating": 0, "client_avg_rating": 0} for date in all_dates}

    reviews_data = (
        ReviewRating.objects.filter(
            driver_id = driver_id, 
            create_at__year=year,
            create_at__month=month)
        .annotate(day=TruncDay('create_at'))
        .values('day')
        .annotate(
            driver_avg_rating=Avg('rating', filter=Q(driver_id__isnull=False)),
            client_avg_rating=Avg('rating', filter=Q(client_id__isnull=False)),
        )
    )

    for review in reviews_data:
        day = review['day'].strftime('%Y-%m-%d')
        statistics[day]['driver_avg_rating'] = round(review['driver_avg_rating'] or 0, 2)
        statistics[day]['client_avg_rating'] = round(review['client_avg_rating'] or 0, 2)

    content = {
        "Message": "Daily average ratings for drivers and clients",
        "Data": statistics
    }
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
def monthly_average_ratings_for_driver(request, driver_id):
    """
    Retrieve monthly average ratings for a specific driver.
    """
    year = int(request.GET.get("year", datetime.now().year))

    statistics = {
        f"{year}-{str(month).zfill(2)}": {"driver_avg_rating": 0, "client_avg_rating": 0}
        for month in range(1, 13)
    }

    reviews_data = (
        ReviewRating.objects.filter(create_at__year=year, driver_id=driver_id)
        .annotate(month=TruncMonth('create_at')) 
        .values('month') 
        .annotate(
            driver_avg_rating=Avg('rating', filter=Q(driver_id__isnull=False)),
            client_avg_rating=Avg('rating', filter=Q(client_id__isnull=False)),
        )
        .order_by('month')
    )

    for review in reviews_data:
        month = review['month'].strftime('%Y-%m')
        statistics[month]['driver_avg_rating'] = round(review['driver_avg_rating'] or 0, 2)
        statistics[month]['client_avg_rating'] = round(review['client_avg_rating'] or 0, 2)

    content = {
        "Message": f"Monthly average ratings for driver {driver_id}",
        "Data": statistics
    }
    return Response(data=content, status=status.HTTP_200_OK)








@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Driver not found'}}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_revenue_by_month_and_year(request, driver_id):
    """
    Retrieve monthly and yearly revenue for a specific driver.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    year = int(request.GET.get("year", datetime.now().year))

    try:
        driver = Drivers.objects.get(id=driver_id)
    except Drivers.DoesNotExist:
        return Response({
            "Message": "Driver not found"
        }, status=status.HTTP_404_NOT_FOUND)

    monthly_revenue = (
        PaymentsDrivers.objects.filter(
            driver_id=driver,
            payments_type=['ride_payment', 'referral_earning'],
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
        'driver_id': driver.id,
        'monthly_revenue': monthly_data,
        'total_revenue': sum(monthly_data.values()),
    }

    return Response({
        "Message": "Driver Revenue by Month and Year",
        "Data": response_data
    }, status=status.HTTP_200_OK)






@extend_schema(
    tags=['BackOffice Driver'], 
    responses={
        200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
        400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
        404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Driver not found'}}}
    }
)
@api_view(['GET'])
def rides_recap_for_driver(request, driver_id: str):
    """
    Retrieve the rides for a specific driver with client name, ride date, and final price for the current month.
    """
    from django.utils.timezone import localtime, now

    try:
        driver = Drivers.objects.get(id=driver_id)
    except Drivers.DoesNotExist:
        return Response({
            "Message": "Driver not found"
        }, status=status.HTTP_404_NOT_FOUND)

    current_time = now()
    current_year = current_time.year
    current_month = current_time.month

    rides = (
        Rides.objects.filter(
            driver_id=driver,
            status="completed", 
            accepted_time__year=current_year,
            accepted_time__month=current_month
        )
        .select_related('client_id')
    )

    ride_data = [
        {
            "client_name": f"{ride.client_id.first_name} {ride.client_id.last_name}",
            "ride_date": localtime(ride.accepted_time).strftime('%Y-%m-%d %H:%M:%S'),
            "final_price": float(ride.final_price),
        }
        for ride in rides
    ]

    return Response({
        "Message": f"Rides for driver {driver_id} (Current Month)",
        "Data": ride_data
    }, status=status.HTTP_200_OK)
