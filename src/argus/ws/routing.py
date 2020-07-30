from django.urls import path

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# from .views import IncidentConsumer, ActiveIncidentConsumer
from .consumers import ActiveIncidentConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("active/", ActiveIncidentConsumer),
        ])
    ),
})

