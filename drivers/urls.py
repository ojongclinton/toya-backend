from django.urls import path
from . import views 
from .api import grades as grades_api
from rest_framework_simplejwt.views import (
    TokenObtainSlidingView,
    TokenRefreshSlidingView,
)


urlpatterns = [
    # Authentication endpoints
    path('auth/register/' , view=views.register_drivers , name ='register_drivers'),
    path('auth/login/' , view=views.login_drivers , name ='login_drivers'),
    path('auth/logout/' , view=views.logout_drivers , name ='logout _drivers'),
    path('auth/forgot_password/' , view=views.forgot_password , name ='forgot_password_client'),
    path('auth/reset_password/' , view=views.reset_password , name ='reset_password_client'),
    path('auth/validate-reset-code/', views.validate_reset_code_drivers, name='validate_reset_code_drivers'),
    path('auth/request-signup-otp/', views.request_signup_otp, name='request_signup_otp_driver'),
    path('auth/verify-signup-otp/', views.verify_signup_otp, name='verify_signup_otp_driver'),
    
    # Profile and vehicle management
    path('profile/' , view=views.profile , name ='drivers_profile'),
    path('update_availability/' , view=views.update_driver_availability , name ='update_driver_availability'),
    path('delete/' , view=views.delete_driver , name ='delete_account_driver'),
    path('vehicle/' , view=views.create_Kyc_driver_vehicle,  name ='create_Kyc_driver_vehicle'),
    path('vehicle/update/' , view=views.update_Kyc_driver_vehicle,  name ='update_Kyc_driver_vehicle'),
    path('vehicle/details/' , view=views.retrieve_vehicle_details,  name ='details_kyc_driver_vehicle'),
    path('vehicle/validation_status' , view=views.get_validation_status_Kyc_driver_vehicle,  name ='get_validation_status_Kyc_driver_vehicle'),
    
    # Driver stats and grades
    path('stats' , view=views.get_stats_drivers , name='get_stats_drivers'), 
    
    # Grade management endpoints
    path('grades' , view=views.get_drivers_grades , name='get_drivers_grades'), 
    path('grades/requirements', view=views.get_all_grades_requirements, name='get_all_grades_requirements'),
    path('grades/evolution' , view=views.get_drivers_grades_evolution , name='get_drivers_grades_evolution'), 
    
    # Admin grade management
    path('admin/grades/', grades_api.list_grades, name='admin_list_grades'),
    path('admin/grades/create/', grades_api.create_grade, name='admin_create_grade'),
    path('admin/grades/<int:grade_id>/', grades_api.update_grade, name='admin_update_grade'),
    path('admin/grades/<int:grade_id>/delete/', grades_api.delete_grade, name='admin_delete_grade'),
    
    # Grade requirements management
    path('admin/grades/<int:grade_id>/requirements/', grades_api.list_grade_requirements, name='admin_list_grade_requirements'),
    path('admin/grades/<int:grade_id>/requirements/add/', grades_api.add_grade_requirement, name='admin_add_grade_requirement'),
    path('admin/requirements/<int:requirement_id>/', grades_api.update_grade_requirement, name='admin_update_grade_requirement'),
    path('admin/requirements/<int:requirement_id>/delete/', grades_api.delete_grade_requirement, name='admin_delete_grade_requirement'),
    
    # Driver grade management
    path('admin/drivers/<uuid:driver_id>/grade/', grades_api.get_driver_grade, name='admin_get_driver_grade'),
    path('admin/drivers/<uuid:driver_id>/grade/update/', grades_api.update_driver_grade, name='admin_update_driver_grade'),
    path('admin/drivers/<uuid:driver_id>/grade/history/', grades_api.get_driver_grade_history, name='admin_get_driver_grade_history'),
    path('admin/drivers/<uuid:driver_id>/grade/evaluate/', grades_api.evaluate_driver_grade, name='admin_evaluate_driver_grade'),

    # JWT token management
    path('token/', TokenObtainSlidingView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshSlidingView.as_view(), name='token_refresh'),
    
    # Profile picture upload
    path('upload/profile_picture/', views.upload_driver_profile_picture, name='upload_driver_profile_picture'),
    
    # Subscription management
    path('subscribe', views.subscribe_driver, name="subscribe_driver"),
    path('subscription-status', views.check_subscription_status, name="check_subscription_status"),
    path('cancel-subscription', views.cancel_subscription, name="cancel_subscription"),
    
    # Development/Testing endpoints
    path('dev/reset/', view=views.reset_driver_account, name='reset_driver_account'),
    path('dev/adjust-wallet/', view=views.adjust_driver_wallet, name='adjust_driver_wallet'),

]
