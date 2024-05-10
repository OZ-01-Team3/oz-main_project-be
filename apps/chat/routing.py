from django.urls import path

from . import consumers, views

websocket_urlpatterns = [
    path("ws/chat/<int:chatroom_id>/", consumers.ChatConsumer.as_asgi()),
    path("", views.ChatRoomView.as_view(), name="chatroom"),
    path("<int:chatroom_id>/", views.ChatDetailView.as_view(), name="chat-detail"),
    path("enter/", views.render_chat),
]
