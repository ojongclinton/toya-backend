from django.urls import path

from .views import *

urlpatterns = [
    path("clients" , view=clients_views.retrieve_all_client , name= 'retrieve_all_client'), 
    path("clients/<str:client_id>" , view=clients_views.retrieve_details_of_client , name= 'retrieve_details_of_client'), 
    path("clients/<str:client_id>/delete" , view=clients_views.delete_client_account , name= 'delete_client_account'), 
    path("clients/<str:client_id>/update" , view=clients_views.update_client_account , name= 'update_client_account'), 
    
    path('clients/stats/rides-daily-stats/<str:client_id>/', clients_daily_ride_count_statistics, name='clients_daily_ride_count_statistics'),
    path('clients/stats/rides-monthly-stats/<str:client_id>/', clients_monthly_ride_count_statistics, name='clients_monthly_ride_count_statistics'),
    path("clients/stats/revenue-monthly/<str:client_id>/" , clients_revenue_by_month_and_year , name= 'clients_revenue_by_month_and_year'),
    path("clients/stats/revenue-daily/<str:client_id>/" , clients_daily_revenue_by_month , name= 'clients_daily_revenue_by_month'),
    path('clients/stats/referrals-daily/<str:client_id>/', client_referrals_by_day, name='client-referrals-daily'),
    path('clients/stats/referrals-monthly/<str:client_id>/',client_referrals_by_month, name='client-referrals-monthly'),



    path("drivers" , view=drivers_views.retrieve_all_drivers , name= 'retrieve_all_driver'), 
    path("drivers/<str:drivers_id>" , view=drivers_views.retrieve_details_of_drivers , name= 'retrieve_details_of_driver'), 
    path("drivers/<str:drivers_id>/delete" , view=drivers_views.delete_drivers_account , name= 'delete_driver_account'), 
    path("drivers/<str:drivers_id>/update" , view=drivers_views.update_drivers_account , name= 'update_driver_account'), 
    path('vehicle/<str:driver_id>/detail' , view=drivers_views.view_vehicle_submission ,  name ='view_vehicle_submission '),
    path('vehicle/<str:driver_id>/approval' , view=drivers_views.approve_vehicle_verification,  name ='approve_vehicle_verification'),
    path('vehicle/<str:driver_id>/reject' , view=drivers_views.reject_vehicle_verification,  name ='reject_vehicle_verification'),
    path('vehicle/<str:driver_id>/validate-document', view=drivers_views.validate_vehicle_document, name='validate_vehicle_document'),
    path('vehicles/pending/',  view=drivers_views.list_of_pending_vehicles, name='list_pending_vehicles'),
    path('vehicles/approved/', view=drivers_views.list_of_approved_vehicles, name='list_approved_vehicles'),
    path('vehicles/rejected/', view=drivers_views.list_of_rejected_vehicles, name='list_rejected_vehicles'),
    path('revenue/', view= drivers_views.drivers_revenue, name='drivers-revenue'),  
    path('drivers/recap/<str:driver_id>/', rides_recap_for_driver, name='rides_recap_for_driver'),


    path('drivers/stats/rides-daily-stats/<str:driver_id>/', driver_daily_ride_count_statistics, name='drivers_daily_ride_stats'),
    path('drivers/stats/rides-monthly-stats/<str:driver_id>/', driver_monthly_ride_count_statistics, name='drivers_monthly_ride_stats'),
    path('drivers/stats/rides-daily-durations/<str:driver_id>/', driver_daily_ride_durations, name='drivers_daily_ride_durations'),
    path('drivers/stats/rides-monthly-durations/<str:driver_id>/', driver_monthly_ride_durations, name='drivers_monthly_ride_durations'),
    path("drivers/stats/ratings-daily/<str:driver_id>/" , driver_average_ratings_daily , name= 'driver_average_ratings_daily'),
    path("drivers/stats/ratings-monthly/<str:driver_id>/" , monthly_average_ratings_for_driver , name= 'monthly_average_ratings_for_driver'),
    path("drivers/stats/revenue-monthly/<str:driver_id>/" , driver_revenue_by_month_and_year , name= 'driver_revenue_by_month_and_year'),

    
    path("rides" , view=rides_views.retrieve_all_rides , name= 'retrieve_all_rides'), 
    path("rides/active", view=rides_views.retrieve_active_rides, name='retrieve_active_rides'),
    path("rides/<str:rides_id>" , view=rides_views.retrieve_details_of_rides , name= 'retrieve_details_of_rides'), 
    path("rides/<str:rides_id>/delete" , view=rides_views.delete_rides_request , name= 'delete_rides_request'), 

    
    path("promotions" , view=promotions_views.retrieve_all_promotions , name= 'retrieve_all_promotions'), 
    path("promotions/create", view=promotions_views.create_promotion , name ='create_promotion'), 
    path("promotions/<str:promotions_id>" , view=promotions_views.retrieve_details_of_promotions , name= 'retrieve_details_of_rides'), 
    path("promotions/<str:promotions_id>/delete" , view=promotions_views.delete_promotions , name= 'delete_promotions'), 
    path("promotions/<str:promotions_id>/update" , view=promotions_views.update_promotion , name= 'update_promotion'), 

    path("applied-promotions/all" , view=promotions_views.list_client_with_applied_promotions , name= 'list_client_with_applied_promotions'), 
    path("applied-promotions/<str:promotions_id>" , view=promotions_views.get_applied_promotions_for_promotion , name= 'get_applied_promotions_for_promotion'), 


    path("fag" , view=fag_views.retrieve_all_fag , name= 'retrieve_all_fag'), 
    path("fag/create", view=fag_views.create_fag , name ='create_fag'), 
    path("fag/<str:fag_id>" , view=fag_views.retrieve_details_of_fag , name= 'retrieve_details_of_Fag'), 
    path("fag/<str:fag_id>/delete" , view=fag_views.delete_fag , name= 'delete_Fag'), 
    path("fag/<str:fag_id>/update" , view=fag_views.update_fag , name= 'update_fag'), 
    
    
    
    path("referrals/clients" , view=referrals_views.retrieve_all_clients_referrals , name= 'retrieve_all_clients_referrals'), 
    path("referrals/drivers" , view=referrals_views.retrieve_all_drivers_referrals , name= 'retrieve_all_drivers_referrals'), 
    path("referrals/drivers/<str:referrals_id>" , view=referrals_views.retrieve_details_of_drivers_referrals , name= 'retrieve_details_of_drivers_referrals'), 
    path("referrals/clients/<str:referrals_id>" , view=referrals_views.retrieve_details_of_clients_referrals , name= 'retrieve_details_of_clients_referrals'), 


    path("stats", view=stats_and_repport_views.global_stats , name ='global_stats'), 
    path("reports/daily" , view=stats_and_repport_views.daily_report , name= 'daily_report'), 
    path("reports/monthly" , view=stats_and_repport_views.monthly_report , name= 'monthly_report'),
    path("reports/yearly" , view=stats_and_repport_views.yearly_report , name= 'yearly_report'),
    path("reports/ride-statistics" , view=stats_and_repport_views.ride_statistics , name= 'ride_statistics'),
    path("reports/promotion-referral-statistics/" , view=stats_and_repport_views.promotion_referral_statistics , name= 'promotion_referral_statistics'),
    path("stats/rides-count" , view=stats_and_repport_views.rides_count , name= 'rides_count'),
    path("stats/ratings" , view=stats_and_repport_views.average_ratings , name= 'average_ratings'),
    path("stats/new-users" , view=stats_and_repport_views.new_users , name= 'new_users'),
    path('stats/unique-referrer', view=stats_and_repport_views.unique_referrer_stats, name='unique_referrer_stats'),
    path('stats/rides-monthly-distance-stats/', stats_and_repport_views.monthly_distance_statistics, name='monthly_distance_statistics'),
    path('stats/monthly-revenue/', stats_and_repport_views.monthly_revenue_statistics, name='monthly_revenue_statistics'),
    path('stats/monthly-ride-count/', stats_and_repport_views.monthly_ride_count_statistics, name='monthly_ride_count_statistics'),
    path('stats/average-ride-duration/', stats_and_repport_views.average_ride_duration_statistics, name='average_ride_duration_statistics'),
    path('stats/monthly-cancelled-rides/', stats_and_repport_views.monthly_cancelled_rides_statistics, name='monthly_cancelled_rides_statistics'),
    path('stats/rides-daily-stats/', daily_ride_count_statistics, name='daily_ride_stats'),
    path('stats/rides-monthly-stats/', monthly_ride_count_statistics, name='monthly_ride_stats'),
    path('stats/rides-cancelled-daily-stats/',daily_cancelled_rides_statistics, name='daily_cancelled_stats'),
    path('stats/rides-cancelled-monthly-stats/', monthly_cancelled_rides_statistics, name='monthly_cancelled_stats'),
    path('stats/rides-daily-durations/', daily_ride_durations, name='daily_ride_durations'),
    path('stats/rides-monthly-durations/', monthly_ride_durations, name='monthly_ride_durations'),

    
    path("support/clients/tickets" , view=supports_views.list_support_tickets_client , name= 'list_support_tickets_client'), 
    path("support/drivers/tickets" , view=supports_views.list_support_tickets_drivers , name= 'list_support_tickets_drivers'),
    
    path("support/clients/tickets/<str:ticket_id>" , view=supports_views.get_support_ticket_clients , name= 'get_support_ticket_clients'), 
    path("support/drivers/tickets/<str:ticket_id>" , view=supports_views.get_support_ticket_drivers , name= 'get_support_ticket_drivers'),
    
    
    path("support/clients/tickets/<str:ticket_id>/close" , view=supports_views.close_support_ticket_clients , name= 'close_support_ticket_clients'), 
    path("support/drivers/tickets/<str:ticket_id>/close" , view=supports_views.close_support_ticket_drivers , name= 'close_support_ticket_drivers'),
    
    path('support/conversation/all', view=get_all_support_conversations , name='retrieve_support_conversation_by_ticket'), 
    path('support/conversation/<str:ticket_id>', view=retrieve_support_conversation_by_ticket , name='retrieve_support_conversation_by_ticket'),
    path('support/conversation/<str:ticket_id>/delete', view=delete_support_conversation, name='delete_support_conversation'),
    
    path('auths/admin/register/',view=auth_views.register_admin , name='register_admin'),
    path('auths/admin/login/',   view=auth_views.login_admin, name='login_admin'),
    path('auths/admin/delete/<str:admin_id>/',   view=auth_views.delete_admin, name='delete_admin'),
    path('auths/admin/list/',   view=auth_views.list_admins, name='list_admins'),
    path('auth/admin/logout/' , view=auth_views.logout_admin , name ='logout_admin'),
    path('upload/profile_picture/',view= auth_views.upload_backoffice_profile_picture, name='upload_backoffice_profile_picture'),
    path('auth/forgot_password/' , view=auth_views.forgot_password , name ='forgot_password_backoffce'),
    path('auth/reset_password/' , view=auth_views.reset_password , name ='reset_password_backoffce'),
    path('auth/validate-reset-code/', auth_views.validate_reset_code_backoffce, name='validate_reset_code_backoffce'),



    

    
    path('payments/clients',   view=payments_views.get_all_payments_client, name='get_all_payments_client'),
    path('payments/clients/<str:payment_id>' , view=payments_views.get_payment_detail_client , name ='get_payment_detail_client'),

    path('payments/drivers',   view=payments_views.get_all_payments_drivers, name='get_all_payments_drivers'),
    path('payments/drivers/<str:payment_id>' , view=payments_views.get_payment_detail_drivers , name ='get_payment_detail_drivers'),


    path('payments/wallet-payments',   view=payments_views.get_wallet_payments, name='get_wallet_payments'),
    path('payments/wallet-payment-stats', payments_views.get_wallet_payment_statistics, name='get_wallet_payment_statistics'),
    path('payments/payment-statistics/',   view=payments_views.payment_statistics, name='payment_statistics'),
    
    
    path('grades/', grades_views.list_grades, name='list_grades'),
    path('grades/create/', grades_views.create_grade, name='create_grade'),
    path('grades/<str:grade_id>/update/', grades_views.update_grade, name='update_grade'),
    path('grades/<str:grade_id>/delete/', grades_views.delete_grade, name='delete_grade'),

]  

