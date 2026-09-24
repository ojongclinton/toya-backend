import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.security.websocket import AllowedHostsOriginValidator
from core.middleware import JWTAuthMiddlewareStack
from conversation.routing import websocket_urlpatterns as conversation_websocket_urlpatterns
from support.routing import websocket_urlpatterns as support_websocket_urlpatterns
from notifications.routing import websocket_urlpatterns as notifications_websocket_urlpatterns
from payments.routing import websocket_urlpatterns as payments_websocket_urlpatterns
from navigation.routing import websocket_urlpatterns as navigation_websocket_urlpatterns
from rides.routing import websocket_urlpatterns as rides_websocket_urlpatterns
from backoffice.routing import websocket_urlpatterns as backoffice_websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

websocket_urlpatterns = (
    conversation_websocket_urlpatterns + 
    support_websocket_urlpatterns + 
    notifications_websocket_urlpatterns + 
    payments_websocket_urlpatterns +
    navigation_websocket_urlpatterns +
    rides_websocket_urlpatterns +
    backoffice_websocket_urlpatterns
)

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        ),
    }
)
