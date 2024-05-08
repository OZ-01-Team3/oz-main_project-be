"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from apps.chat.routing import websocket_urlpatterns as chat_routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.settings")

application = ProtocolTypeRouter({"http": django_asgi_app, "websocket": AuthMiddlewareStack(URLRouter(chat_routing))})
