
from django.contrib import admin
from django.urls import path , include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from . import config_mobile, config_backoffice
from django.conf import settings
from django.conf.urls.static import static
from core.firebase.firebase_views import * 

urlpatterns = [
    
    path('admin/', admin.site.urls),
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
    path('api/backoffice/', include('backoffice.urls')),
    path('api/firebase/register-device/', register_device_view, name='register_device'),


    
    
    # Documentation Swagger for  the   mobile part
    path('api/schema/mobile/', SpectacularAPIView.as_view(urlconf=config_mobile), name='schema-mobile'),
    path('api/docs/mobile/swagger/', SpectacularSwaggerView.as_view(url_name='schema-mobile'), name='swagger-mobile'),
    path('api/docs/mobile/redoc/', SpectacularRedocView.as_view(url_name='schema-mobile'), name='redoc-mobile'),

    # Documentation Swagger for  the   Backoffice part
    path('api/schema/backoffice/', SpectacularAPIView.as_view(urlconf=config_backoffice), name='schema-backoffice'),
    path('api/docs/backoffice/swagger/', SpectacularSwaggerView.as_view(url_name='schema-backoffice'), name='swagger-backoffice'),
    path('api/docs/backoffice/redoc/', SpectacularRedocView.as_view(url_name='schema-backoffice'), name='redoc-backoffice'),
] 

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)