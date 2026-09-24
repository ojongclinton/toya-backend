from django.urls import path 
from . import views

urlpatterns = [
    path("all", view=views.get_all_active_promotion , name ='get_all_active_promotion'), 
    path("apply", view=views.client_apply_for_active_promotion , name ='client_apply_for_active_promotion'), 
]
