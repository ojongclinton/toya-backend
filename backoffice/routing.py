from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/backoffice/', consumers.BackofficeConsumer.as_asgi()),
]