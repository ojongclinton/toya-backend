from django.urls import path 
from . import views


urlpatterns = [
    
    path("all", view=views.get_all_notification , name='get_all_notification'),
    path('bulk-delete', views.bulk_delete_notifications, name='bulk-delete-notifications'),
    path('<str:notification_id>/mark_as_read', views.mark_notifications_read, name='notification-mark-read'),
    path('<str:notification_id>', views.obtain_notifications, name='obtain_notifications'),
]

