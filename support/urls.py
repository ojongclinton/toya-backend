from django.urls import path 
from . import views 

urlpatterns = [
    path("driver/contact" , view=views.create_support_ticket_drivers , name='create_support_ticket_drivers'), 
    path("client/contact" , view=views.create_support_ticket_clients , name='create_support_ticket_clients'), 
    path("client/tickets", view=views.get_client_support_tickets, name='get_client_support_tickets'),
    path("driver/tickets", view=views.get_driver_support_tickets, name='get_driver_support_tickets'),
    path('all', view=views.get_user_support_conversations , name='get_user_support_conversations'), 
    path("faq/drivers" , view=views.driver_get_all_fag , name='driver_get_all_fag'), 
    path("faq/client" , view=views.client_get_all_fag , name='client_get_all_fag'), 
    path('<str:ticket_id>', view=views.retrieve_support_conversation_by_ticket , name='retrieve_support_conversation_by_ticket'),
    path('language/set', view=views.set_language, name='set_language'),
    path('language/get', view=views.get_language, name='get_language'),
    
]
