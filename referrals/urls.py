from django.urls import path
from . import views


urlpatterns = [
    path("clients/all", view=views.get_all_clients_referrals , name = 'get_all_clients_referrals'), 
    path("clients/apply", view=views.apply_clients_referrals , name = 'apply_clients_referrals'), 
    path('clients/referral-earnings', view= views.client_get_referral_earnings , name = "client_get_referral_earnings" ), 

    path("drivers/all", view=views.get_all_drivers_referrals , name = 'get_all_drivers_referrals') , 
    path("drivers/apply", view=views.apply_drivers_referrals , name = 'apply_drivers_referrals') , 
    path('drivers/referral-earnings', view= views.drivers_get_referral_earnings , name = "drivers_get_referral_earnings" ), 

]
