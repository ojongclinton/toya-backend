from django.urls import path
from . import views 
from rest_framework_simplejwt.views import (
    TokenObtainSlidingView,
    TokenRefreshSlidingView,
)


urlpatterns = [
    path('auth/register/' , view=views.register_client , name ='register_client'),
    path('auth/login/' , view=views.login_client , name ='login_client'),
    path('auth/logout/' , view=views.logout_client , name ='logout _client'),
    path('auth/forgot_password/' , view=views.forgot_password , name ='forgot_password_client'),
    path('auth/reset_password/' , view=views.reset_password , name ='reset_password_client'),
    path('auth/validate-reset-code/', views.validate_reset_code_clients, name='validate_reset_code_clients'),
    path('auth/request-signup-otp/', views.request_signup_otp, name='request_signup_otp_client'),
    path('auth/verify-signup-otp/', views.verify_signup_otp, name='verify_signup_otp_client'),


    
    path('profile/' , view=views.profile , name ='client_profile'),
    path('delete/' , view=views.delete_client , name ='delete_account_client'),
    
    
    path('token/', TokenObtainSlidingView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshSlidingView.as_view(), name='token_refresh'),
    
    
    path('stats' , view=views.get_stats_client , name='get_stats_client'), 
    path('upload/profile_picture/',view = views.upload_clients_profile_picture, name='upload_clients_profile_picture'),

    path('test_sms/', view=views.test_sms, name='test_sms'),
    
    # Development/Testing endpoints
    path('dev/reset/', view=views.reset_client_account, name='reset_client_account'),
]
