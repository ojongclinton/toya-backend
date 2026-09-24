from django.urls import path 
from . import views 


urlpatterns = [
    path('all', view=views.get_user_conversations, name='get_user_conversations'),
    path('delete-all', view=views.delete_all_conversations, name='delete_all_conversations'),
    path('<str:rides_id>', view=views.get_conversation_by_ride, name='get_conversation_by_ride'),
    path('<str:rides_id>/delete', view=views.delete_conversation_by_ride, name='delete_conversation_by_ride'),
]