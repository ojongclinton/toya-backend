from django.urls import path 
from . import views 

urlpatterns = [

    path('wallet/make-deposit', view= views.driver_make_deposit_to_his_wallet_account , name = "driver_make_deposit_to_his_wallet_account" ), 
    path('wallet/history', view= views.driver_get_all_retrieve_wallet_account , name = "driver_get_all_retrieve_wallet_account" ), 
    path('wallet/detail/<str:transaction_id>', view= views.driver_get_details_retrieve_wallet_account , name = "driver_get_details_retrieve_wallet_account" ), 
    path('wallet/check-status', view= views.check_payment_status , name = "check_payment_status" ),
    path('wallet/manage-payment-numbers/', views.driver_manage_payment_numbers, name='driver-manage-payment-numbers'),
    path('wallet/add-payment-phone-number/', views.add_payment_phone_number, name='add-payment-phone-number'),

]
 

