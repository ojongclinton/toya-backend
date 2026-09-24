from django.urls import path 
from . import views

urlpatterns = [
    path("pickup/<str:rides_id>", view=views.pickup , name="pickup"), 
    path("dropoff/<str:rides_id>", view=views.dropoff , name="dropoff"),
    # path("distance-matrix", view=views.distance_matrix , name="distance_matrix"), 
    path("clients/nearby-drivers/<str:rides_id>", view=views.nearby_drivers_for_a_ride , name=" nearby_drivers_for_a_ride"), 
    path("send-driver-location", view=views.update_driver_location , name= 'update_driver_location' ),
    
    path("available-drivers", view=views.available_drivers_on_map, name='available_drivers_on_map'),
    path("hot-zones", view=views.hot_zones, name='hot_zones'),
]



