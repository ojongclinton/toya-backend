from django.urls import re_path
from .consumers import RideStatusConsumer

websocket_urlpatterns = [
    re_path(r'ws/ride-status/$', RideStatusConsumer.as_asgi()),
]
