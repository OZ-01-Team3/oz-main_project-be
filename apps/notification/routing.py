from django.urls import path

from . import consumers, views

websocket_urlpatterns = [
    path("ws/notification/", consumers.NotificationConsumer.as_asgi()),
]
