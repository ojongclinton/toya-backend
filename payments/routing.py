from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/payment/status/(?P<transaction_id>[\w-]+)/(?P<user_id>[\w-]+)/$', consumers.PaymentStatusConsumer.as_asgi()),
]
