"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from public_chat.consumers import PublicChatConsumer
from chat.consumers import PrivateChatConsumer
from notifications.consumers import NotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path('', NotificationConsumer.as_asgi()),
                path('public_chat/<str:room_id>/', PublicChatConsumer.as_asgi(), name='public-chat'),
                path('chat/<str:room_id>/', PrivateChatConsumer.as_asgi(), name='private-chat'),
            ])
        )
    ),
    # Just HTTP for now. (We can add other protocols later.)
})