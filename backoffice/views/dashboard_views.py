# backoffice/views/dashboard_views.py (à créer)

from rides.models import Rides


@extend_schema(tags=['Dashboard'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    """
    Vue d'ensemble complète du dashboard
    Retourne toutes les métriques principales
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count, Sum, Avg, Q
    
    _, user = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # COURSES
    rides_today = Rides.objects.filter(created_at__date=today)
    rides_yesterday = Rides.objects.filter(created_at__date=yesterday)
    
    rides_stats = {
        "in_progress": Rides.objects.filter(status='in_progress').count(),
        "completed_today": rides_today.filter(status='completed').count(),
        "cancelled_today": rides_today.filter(status='cancelled').count(),
        "pending": Rides.objects.filter(status='pending').count(),
        "total_today": rides_today.count(),
        "change_vs_yesterday": rides_today.count() - rides_yesterday.count()
    }
    
    # REVENUS
    revenue_today = rides_today.filter(status='completed').aggregate(
        total=Sum('final_price')
    )['total'] or 0
    
    revenue_yesterday = rides_yesterday.filter(status='completed').aggregate(
        total=Sum('final_price')
    )['total'] or 1  # Éviter division par zéro
    
    revenue_week = Rides.objects.filter(
        created_at__date__gte=week_ago,
        status='completed'
    ).aggregate(total=Sum('final_price'))['total'] or 0
    
    revenue_month = Rides.objects.filter(
        created_at__date__gte=month_ago,
        status='completed'
    ).aggregate(total=Sum('final_price'))['total'] or 0
    
    revenue_stats = {
        "today": float(revenue_today),
        "yesterday": float(revenue_yesterday),
        "week": float(revenue_week),
        "month": float(revenue_month),
        "change_percent": round(((revenue_today - revenue_yesterday) / revenue_yesterday) * 100, 1)
    }
    
    # CHAUFFEURS
    drivers_online = Drivers.objects.filter(is_available=True).count()
    drivers_in_ride = Rides.objects.filter(
        status='in_progress'
    ).values('driver_id').distinct().count()
    drivers_total = Drivers.objects.count()
    
    drivers_stats = {
        "online": drivers_online,
        "in_ride": drivers_in_ride,
        "offline": drivers_total - drivers_online,
        "total": drivers_total
    }
    
    # CLIENTS
    clients_today = Clients.objects.filter(date_joined__date=today).count()
    clients_active_today = rides_today.values('client_id').distinct().count()
    clients_total = Clients.objects.count()
    
    clients_stats = {
        "active_today": clients_active_today,
        "new_today": clients_today,
        "total": clients_total
    }
    
    # ZONES CHAUDES (top 5)
    from navigation.views import hot_zones
    hot_zones_data = []  # Appeler l'endpoint existant ou récupérer directement
    
    return Response({
        "Message": "Dashboard overview",
        "Data": {
            "rides": rides_stats,
            "revenue": revenue_stats,
            "drivers": drivers_stats,
            "clients": clients_stats,
            "timestamp": timezone.now().isoformat()
        }
    }, status=status.HTTP_200_OK)