from django.urls import path

from apps.chat import views

urlpatterns = [
    path("", views.ChatRoomView.as_view(), name="chatroom"),
    path("<int:chatroom_id>/", views.ChatDetailView.as_view(), name="chat-detail"),
    path("enter/", views.render_chat)
]
