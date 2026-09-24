from django.urls import path 
from . import views


urlpatterns = [
    path('current/<str:rides_id>', view=views.current_rides , name ='current_rides') , 
    
    path('client/request/', view=views.client_request_rides , name ='client_request_rides') , 
    path('client/cancel/<str:rides_id>', view=views.client_cancel_rides , name ='client_cancel_rides') ,
    path('client/estimate', view=views.client_estimate_rides , name='client_estimate_rides'),
    path('client/track/<str:rides_id>', view=views.client_track_rides , name='client_track_rides'),
    path('client/profile/<str:drivers_id>', views.driver_profile_for_client, name='driver-profile-for-client'),
    path('driver/profile/<str:clients_id>', views.client_profile_for_driver, name='client-profile-for-driver'),


    path('driver/<str:rides_id>/complete', view=views.driver_complete_rides , name='driver_complete_rides'),
    path('driver/<str:rides_id>/accept', view=views.driver_accept_rides , name='driver_accept_rides'),
    path('driver/<str:rides_id>/cancel', view=views.driver_cancel_rides , name='driver_cancel_rides'),
    path('driver/<str:rides_id>/start', view=views.driver_start_rides , name='driver_start_rides'),
    path('driver/pending', view=views.get_all_rides_pending , name='get_all_rides_pending'),
    path('driver/<str:rides_id>/accepted/', views.accepted_driver, name='accepted_driver'),

    path('driver/details/<str:rides_id>', view=views.get_driver_rides_details , name='get_rides_details'),
    path('driver/history', view=views.get_all_driver_rides_history , name='get_all_driver_rides_history'),
    
    path('client/details/<str:rides_id>', view=views.get_client_rides_details , name='get_client_rides_details'),
    path('client/history', view=views.get_all_client_ride_history , name='get_all_client_ride_history'),
    
    path('review/all', view=views.driver_get_all_review_rating , name='driver_get_all_review_rating'), 
    path('client/review/', view=views.client_create_review_rating , name='create_review_rating'), 
    path('driver/review/', view=views.drivers_create_review_rating , name='drivers_review_rating'), 


    path('driver/current-ride', view=views.driver_get_current_ride, name='driver_current_ride'),
    path('client/current-ride', view=views.client_get_current_ride, name='client_current_ride'),
]


