
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from clients.models import Clients 
from drivers.models import Drivers 
from rides.models import Rides , ReviewRating
from payments.models import  PaymentsDrivers , PaymentsClients 
from referrals.models import ReferralsClient , ReferralsDrivers
from promotions.models import ApplyPromotions
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
from ..customs import Utils
from django.db.models.functions import TruncDay



@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_stats(request):
    """
    Retrieve global statistics for users, drivers, rides, and payments.
    """
    try:
        token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    except Exception as e:
        return Response({"Message": "Invalid or missing token", "Error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    all_count_user_client = Clients.objects.count() or 0
    all_count_user_driver = Drivers.objects.count() or 0
    all_count_user = all_count_user_client + all_count_user_driver

    if all_count_user > 0:
        percentage_client = (all_count_user_client / all_count_user) * 100
        percentage_driver = (all_count_user_driver / all_count_user) * 100
    else:
        percentage_client = 0
        percentage_driver = 0

    client_total_payment = PaymentsClients.objects.aggregate(total=Sum('amount'))['total'] or 0

    driver_total_payments = PaymentsDrivers.objects.filter(payments_type='wallet_pay').aggregate(total=Sum('amount'))['total'] or 0
    driver_subscription_payments = PaymentsDrivers.objects.filter(payments_type='driver_subscription').aggregate(total=Sum('amount'))['total'] or 0

    referral_earning = PaymentsDrivers.objects.filter(payments_type='referral_earning').aggregate(total=Sum('amount'))['total'] or 0

    transaction_total = client_total_payment + driver_total_payments + driver_subscription_payments
    benefice_total = driver_total_payments + driver_subscription_payments

    stats = {
        "total_users": all_count_user,
        "total_drivers": all_count_user_driver,
        "total_rides completed": Rides.objects.filter(status = 'completed').count(),
        "transaction_total": transaction_total,
        "total_rides_amount": client_total_payment,
        "total_expenses": referral_earning,
        "benefice_total": benefice_total,
        "user_distribution": {
            "client_percentage": round(percentage_client, 2),
            "driver_percentage": round(percentage_driver, 2),
        },
    }

    return Response(
        {
            "Message": "Global Statistics Retrieved Successfully",
            "Data": stats,
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_report(request):
    """Generate a daily report on activities, revenue, and ride statistics."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    today = datetime.now().date()
        
    stats = { 
        'rides_today': Rides.objects.filter(status = 'completed' , start_time__date=today).count() or 0,
        'revenue_today': PaymentsClients.objects.filter(create_at__date=today).aggregate(total=Sum('amount'))['total'] or 0,
        'report_date': today.isoformat(),
    }
    
    return Response({"Message": "Daily Report", "Data": stats}, status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def monthly_report(request):
    """
    Generate a monthly report on activities, revenue, and ride statistics.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    last_day_of_month = monthrange(now.year, now.month)[1]
    end_of_month = now.replace(day=last_day_of_month, hour=23, minute=59, second=59, microsecond=999999)

    stats = {
        "rides_this_month": Rides.objects.filter(status = 'completed' ,  start_time__gte=start_of_month, start_time__lte=end_of_month).count() or 0,
        "revenue_this_month": PaymentsDrivers.objects.filter(
            create_at__gte=start_of_month, create_at__lte=end_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }

    return Response(
        {
            "Message": "Monthly Report",
            "Start_Date": start_of_month.isoformat(),
            "End_Date": end_of_month.isoformat(),
            "Data": stats,
        },
        status=status.HTTP_200_OK,
    )



@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def yearly_report(request):
    """Generate a yearly report on activities, revenue, and ride statistics."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    now = datetime.now()
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_year = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)

    stats = {
        "rides_this_year": Rides.objects.filter(status = 'completed' , start_time__gte=start_of_year, start_time__lte=end_of_year).count() or 0,
        "revenue_this_year": PaymentsDrivers.objects.filter(
            create_at__gte=start_of_year, create_at__lte=end_of_year
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    return Response(
        {
            "Message": "Yearly Report",
            "Start_Date": start_of_year.isoformat(),
            "End_Date": end_of_year.isoformat(),
            "Data": stats,
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def rides_count(request):
    """Retrieve the total number of rides completed."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    total_rides = Rides.objects.filter(status = 'completed').count() or 0,
    return Response({"Message": "Total Rides", "Data": total_rides}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def average_ratings(request):
    """Retrieve daily average ratings for drivers and clients."""
    year = int(request.GET.get("year", datetime.now().year))
    month = int(request.GET.get("month", datetime.now().month))

    start_date = datetime(year, month, 1)
    next_month = start_date + timedelta(days=31)
    end_date = datetime(next_month.year, next_month.month, 1) - timedelta(days=1)
    all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    statistics = {date.strftime('%Y-%m-%d'): {"driver_avg_rating": 0, "client_avg_rating": 0} for date in all_dates}

    reviews_data = (
        ReviewRating.objects.filter(create_at__year=year, create_at__month=month)
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
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def new_users(request):
    """Retrieve the count of new clients and drivers registered in the last month."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    today = datetime.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    client_daily_counts = Clients.objects.filter(date_joined__gte=start_of_month, date_joined__lte=end_of_month) \
        .annotate(date=TruncDate('date_joined')) \
        .values('date') \
        .annotate(count=Count('id')) \
        .order_by('date')

    driver_daily_counts = Drivers.objects.filter(date_joined__gte=start_of_month, date_joined__lte=end_of_month) \
        .annotate(date=TruncDate('date_joined')) \
        .values('date') \
        .annotate(count=Count('id')) \
        .order_by('date')

    daily_stats = {}
    for data in client_daily_counts:
        date_str = data['date'].strftime("%Y-%m-%d")
        daily_stats.setdefault(date_str, {"clients": 0, "drivers": 0})["clients"] = data['count']

    for data in driver_daily_counts:
        date_str = data['date'].strftime("%Y-%m-%d")
        daily_stats.setdefault(date_str, {"clients": 0, "drivers": 0})["drivers"] = data['count']

    sorted_stats = {date: daily_stats[date] for date in sorted(daily_stats)}

    return Response({
        "Message": "New Users Daily Report",
        "Start_Date": start_of_month.strftime("%Y-%m-%d"),
        "End_Date": end_of_month.strftime("%Y-%m-%d"),
        "Data": sorted_stats
    }, status=status.HTTP_200_OK)
    
    
    

    

@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def unique_referrer_stats(request):
    """Retrieve unique referrer stats for drivers and clients."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    driver_referrer_stats = ReferralsDrivers.objects.values('referrer_driver_id').annotate(
        referral_count=Count('referred_driver_id')
    ).annotate(
        unique_referrer_count=Count('referrer_driver_id', distinct=True)
    )
    
    total_unique_drivers = driver_referrer_stats.count()

    client_referrer_stats = ReferralsClient.objects.values('referrer_client_id').annotate(
        referral_count=Count('referred_client_id')
    ).annotate(
        unique_referrer_count=Count('referrer_client_id', distinct=True)
    )
    
    total_unique_clients = client_referrer_stats.count()

    stats = {
        'driver_referrer_stats': list(driver_referrer_stats),
        'total_unique_drivers': total_unique_drivers,
        'client_referrer_stats': list(client_referrer_stats),
        'total_unique_clients': total_unique_clients,
    }

    return Response({"Message": "Unique Referrer Stats", "Data": stats}, status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def ride_statistics(request):
    """Retrieve ride statistics for daily, weekly, and monthly reports for charting."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    today = datetime.now().date()
    
    last_30_days = [today - timedelta(days=i) for i in range(30)]
    
    daily_data = {
        'dates': [],
        'total_rides': [],
        'total_revenue': [],
        'client_count': [],
        'driver_count': []
    }
    
    for single_date in last_30_days:
        daily_rides = Rides.objects.filter(start_time__date=single_date)
        daily_revenue = PaymentsClients.objects.filter(rides_id__in=daily_rides).aggregate(total=Sum('amount'))['total'] or 0
        
        daily_data['dates'].append(single_date.strftime('%Y-%m-%d'))
        daily_data['total_rides'].append(daily_rides.count())
        daily_data['total_revenue'].append(daily_revenue)
        daily_data['client_count'].append(Clients.objects.filter(id__in=daily_rides.values_list('client_id', flat=True)).distinct().count())
        daily_data['driver_count'].append(Drivers.objects.filter(id__in=daily_rides.values_list('driver_id', flat=True)).distinct().count())

    weekly_data = {
        'week_start_dates': [],
        'total_rides': [],
        'total_revenue': []
    }

    for week in range(4):  
        week_start = today - timedelta(weeks=week + 1)
        weekly_rides = Rides.objects.filter(start_time__date__gte=week_start, start_time__date__lt=week_start + timedelta(weeks=1))
        weekly_revenue = PaymentsClients.objects.filter(rides_id__in=weekly_rides).aggregate(total=Sum('amount'))['total'] or 0
        
        weekly_data['week_start_dates'].append(week_start.strftime('%Y-%m-%d'))
        weekly_data['total_rides'].append(weekly_rides.count())
        weekly_data['total_revenue'].append(weekly_revenue)


    monthly_data = {
        'month_names': [],
        'total_rides': [],
        'total_revenue': []
    }

    for month in range(1, 13): 
        month_start = today.replace(day=1, month=month) if month <= today.month else today.replace(day=1, month=month-1)
        monthly_rides = Rides.objects.filter(start_time__month=month, start_time__year=today.year)
        monthly_revenue = PaymentsClients.objects.filter(rides_id__in=monthly_rides).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_data['month_names'].append(month_start.strftime('%B'))
        monthly_data['total_rides'].append(monthly_rides.count())
        monthly_data['total_revenue'].append(monthly_revenue)
    
    monthly_data['month_names'][-1] = "December"
    
    response_data = {
        'daily_stats': daily_data,
        'weekly_stats': weekly_data,
        'monthly_stats': monthly_data
    }
    
    return Response({"Message": "Ride Statistics", "Data": response_data}, status=status.HTTP_200_OK)








@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def promotion_referral_statistics(request):
    """Retrieve promotion and referral statistics for daily, weekly, and monthly reports for charting."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    today = datetime.now().date()
    
    last_30_days = [today - timedelta(days=i) for i in range(30)]
    
    daily_data = {'dates': [], 'promotions_applied': [], 'referrals_count': []}
    
    for single_date in last_30_days:
        daily_promotions = ApplyPromotions.objects.filter(applied_at__date=single_date)
        daily_referrals = ReferralsClient.objects.filter(create_at__date=single_date).count() + ReferralsDrivers.objects.filter(create_at__date=single_date).count()

        daily_data['dates'].append(single_date.strftime('%Y-%m-%d'))
        daily_data['promotions_applied'].append(daily_promotions.count())
        daily_data['referrals_count'].append(daily_referrals)

    weekly_data = {'week_start_dates': [], 'promotions_applied': [], 'referrals_count': []}
    
    for week in range(4):
        week_start = today - timedelta(weeks=week + 1)
        weekly_promotions = ApplyPromotions.objects.filter(applied_at__date__gte=week_start, applied_at__date__lt=week_start + timedelta(weeks=1))
        weekly_referrals = ReferralsClient.objects.filter(create_at__gte=week_start, create_at__lt=week_start + timedelta(weeks=1)).count() + \
                          ReferralsDrivers.objects.filter(create_at__gte=week_start, create_at__lt=week_start + timedelta(weeks=1)).count()
        
        weekly_data['week_start_dates'].append(week_start.strftime('%Y-%m-%d'))
        weekly_data['promotions_applied'].append(weekly_promotions.count())
        weekly_data['referrals_count'].append(weekly_referrals)

    monthly_data = {'month_names': [], 'promotions_applied': [], 'referrals_count': []}
    
    for month in range(1, 13):  
        monthly_promotions = ApplyPromotions.objects.filter(applied_at__month=month, applied_at__year=today.year)
        monthly_referrals = ReferralsClient.objects.filter(create_at__month=month, create_at__year=today.year).count() + \
                            ReferralsDrivers.objects.filter(create_at__month=month, create_at__year=today.year).count()
        
        monthly_data['month_names'].append((today.replace(month=month)).strftime('%B'))
        monthly_data['promotions_applied'].append(monthly_promotions.count())
        monthly_data['referrals_count'].append(monthly_referrals)

    response_data = {
        'daily_stats': daily_data,
        'weekly_stats': weekly_data,
        'monthly_stats': monthly_data
    }
    
    return Response({"Message": "Promotion and Referral Statistics", "Data": response_data}, status=status.HTTP_200_OK)



@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def monthly_distance_statistics(request):
    """
    Retrieve monthly statistics for the total distance traveled, segmented by type of service.
    """
    token, users = JWT.filter_and_decode_token(request.headers.get("Authorization"))
 
    current_date = timezone.now()
    current_year = current_date.year
    current_month = current_date.month

    all_days = Utils().generate_dates_for_month(current_year, current_month)

    rides_data = (
        Rides.objects.filter(
            accepted_time__year=current_year,
            accepted_time__month=current_month,
            status="completed"  
        )
        .annotate(day=TruncDay('accepted_time')) 
        .values('day', 'prestation')
        .annotate(total_distance=Sum('distance'))  
        .order_by('day', 'prestation')
    )

    statistics = {day.strftime('%Y-%m-%d'): {"economy": 0, "confort": 0, "prestige": 0} for day in all_days}
    print("pass")
    for ride in rides_data:
        day = ride['day'].strftime('%Y-%m-%d') 
        prestation = ride['prestation']
        distance = ride['total_distance']

        statistics[day][prestation] = distance

    content = {
        "Message": "Daily distance statistics by type of service (Km)",
        "Data": statistics
    }
    return Response(data=content, status=status.HTTP_200_OK)





@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )
@api_view(['GET'])
@permission_classes([IsAuthenticated])

def monthly_revenue_statistics(request):
    """Retrieve monthly revenue statistics by prestation type for completed rides."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year

    revenue_data = (
        Rides.objects.filter(
            accepted_time__year=current_year,
            status="completed" 
        )
        .annotate(month=TruncMonth('accepted_time'))
        .values('month', 'prestation')
        .annotate(total_revenue=Sum('final_price'))
        .order_by('month', 'prestation')
    )

    statistics = {}
    for ride in revenue_data:
        month = ride['month'].strftime('%Y-%m')
        prestation = ride['prestation']
        revenue = ride['total_revenue']

        if month not in statistics:
            statistics[month] = {}
        statistics[month][prestation] = revenue

    return Response({
        "Message": "Monthly revenue statistics by prestation (completed rides only)",
        "Data": statistics
    })


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
    """Retrieve monthly ride count statistics by prestation type for completed rides."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

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

    statistics = {}
    for ride in ride_count_data:
        month = ride['month'].strftime('%Y-%m')
        prestation = ride['prestation']
        total_rides = ride['total_rides']

        if month not in statistics:
            statistics[month] = {}
        statistics[month][prestation] = total_rides

    return Response({
        "Message": "Monthly ride count statistics by prestation (completed rides only)",
        "Data": statistics
    })


@extend_schema(
    tags=['BackOffice Statistics & Reports'], 
    responses={
            200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
            400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
            404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def average_ride_duration_statistics(request):
    """Retrieve average ride duration statistics per month by prestation type for completed rides."""
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

    current_year = timezone.now().year

    duration_data = (
        Rides.objects.filter(
            accepted_time__year=current_year,
            status="completed"
        )
        .annotate(month=TruncMonth('accepted_time'))
        .annotate(duration=ExpressionWrapper(F('end_time') - F('start_time'), output_field=DurationField()))
        .values('month', 'prestation')
        .annotate(average_duration=Avg('duration'))
        .order_by('month', 'prestation')
    )

    statistics = {}
    for ride in duration_data:
        month = ride['month'].strftime('%Y-%m')
        prestation = ride['prestation']
        avg_duration = ride['average_duration']

        if month not in statistics:
            statistics[month] = {}
        statistics[month][prestation] = avg_duration

    return Response({
        "Message": "Average ride duration statistics by prestation (completed rides only)",
        "Data": statistics
    })



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
    token , users = JWT.filter_and_decode_token(request.headers.get("Authorization"))

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

    statistics = {ride['month'].strftime('%Y-%m'): ride['cancelled_rides'] for ride in cancelled_data}

    return Response({
        "Message": "Monthly cancelled rides statistics",
        "Data": statistics
    })




# @extend_schema(
#     tags=['BackOffice Statistics & Reports'], 
#     responses={
#             200: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Operation successful'}}}, 
#             400: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Invalid request parameters'}}},
#             404: {'type': 'object', 'properties': {'Message': {'type': 'string', 'example': 'Resource not found'}}}}
#     )
# @api_view(['GET'])

# def total_revenue(request):
#     """Retrieve the total revenue generated by the application."""
#     total_revenue = Payments.objects.aggregate(total=Sum('amount'))['total'] or 0
#     return Response({"Message": "Total Revenue", "Data": total_revenue}, status=status.HTTP_200_OK)


