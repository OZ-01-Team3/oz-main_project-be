import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework import status
from rest_framework.response import Response

from apps.account.models import Account


class ChatConsumer(AsyncWebsocketConsumer):
    @sync_to_async
    def create_chatroom(self) -> None:
        self.room_name = self.scope["url_route"]["kwargs"][""]

    async def connect(self) -> None:
        pass
