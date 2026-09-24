
from django.urls import path , include
from core.firebase.firebase_views import * 


urlpatterns = [
    path('api/clients/', include('clients.urls')),
    path('api/rides/', include('rides.urls')), 
    path('api/drivers/', include('drivers.urls')), 
    path('api/support/', include('support.urls')), 
    path('api/conversation/', include('conversation.urls')), 
    path('api/notifications/', include('notifications.urls')),
    path('api/promotions/', include('promotions.urls')),
    path('api/referrals/', include('referrals.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/navigation/', include('navigation.urls')),
    path('api/firebase/register-device/', register_device_view, name='register_device'),


]
