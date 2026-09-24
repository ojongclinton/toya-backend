from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/support/(?P<room_name>[^/]+)/$', consumers.SupportConsumer.as_asgi()),

]