# routing.py
from django.urls import re_path
from .consumers import RideTrackingConsumer

websocket_urlpatterns = [
    re_path(r'ws/ride-tracking/(?P<ride_id>[^/]+)/$', RideTrackingConsumer.as_asgi()),
]
