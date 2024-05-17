import base64
import logging
from typing import Any, Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.files.base import ContentFile
from django.http import QueryDict
from django_redis import get_redis_connection

from apps.chat.models import Chatroom, Message
from apps.chat.serializers import MessageSerializer
from apps.chat.utils import check_entered_chatroom, check_opponent_online
from apps.user.models import Account

logger = logging.getLogger(__name__)
redis_conn = get_redis_connection("default")


class ChatConsumer(AsyncJsonWebsocketConsumer):  # type: ignore
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.chat_group_name = ""
        self.chatroom_id = ""
        self.user = ""

    # 소켓에 연결
    async def connect(self) -> None:
        try:
            # scope로 채팅방 id 가져오기
            self.chatroom_id = self.scope["url_route"]["kwargs"]["chatroom_id"]
            self.chat_group_name = self.get_group_name(int(self.chatroom_id))

            chatroom = await self.get_chatroom(self.chatroom_id)

            if chatroom is None:
                await self.close(code=1008, reason="해당 채팅방이 존재하지 않습니다.")
            self.user = self.scope["user"]
            if not await database_sync_to_async(check_entered_chatroom)(chatroom, self.user):
                await self.close(code=1008, reason="해당 채팅방에 존재하는 유저가 아닙니다.")
            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
            await self.accept()
            if check_opponent_online(self.chat_group_name):
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        "type": "alert",
                        "opponent_state": "online",
                    },
                )
            else:
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        "type": "alert",
                        "opponent_state": "offline",
                    },
                )
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason=str(e))

    async def receive_json(self, content: dict[str, Any], **kwargs: Any) -> None:
        """
        클라이언트로 부터 입력받은 메시지를 받고 데이터 서버에 저장,
        그룹 접속자에게 메시지를 전달
        """
        try:
            # 수신된 JSON에서 필요한 데이터를 가져옴
            message = content.get("message")
            image = content.get("image")

            # 데이터 베이스에 Message로 저장할 데이터
            data = {"message": message, "sender": self.user, "chatroom_id": self.chatroom_id}

            # 수신한 데이터에서 이미지가 있으면 base64 디코딩 후 이미지필드로 저장
            if image:
                image_data = self.decode_image(image)
                data["image"] = image_data

            # 만약 그룹에 속한 멤버가 2명이면 메시지는 무조건 읽은것으로 상태저장
            # django-redis를 사용해서 그룹에 속한 멤버의 수를 가져옴
            if check_opponent_online(self.chat_group_name):
                data["status"] = False
            chat = await self.save_chat_message(**data)

            # 저장된 메시지를 직렬화
            data = MessageSerializer(chat).data
            data["message"] = data.pop("text")
            data["type"] = "chat_message"
            # 수신된 메시지와 정보를 그룹에 속한 채팅 참가자들에게 보내기
            await self.channel_layer.group_send(self.chat_group_name, data)
        # 예외 발생 시 내용을 json으로 보내줌
        except ValueError as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1003, reason=str(e))
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason=str(e))

    # 소켓 연결 해제
    async def disconnect(self, close_code: int) -> None:
        chat_group_name = self.get_group_name(int(self.chatroom_id))
        await self.channel_layer.group_discard(chat_group_name, self.channel_name)

    async def alert(self, event: dict[str, Any]) -> None:
        try:
            await self.send_json(event)
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason=str(e))

    async def chat_message(self, event: QueryDict) -> None:
        """
        그룹으로부터 수신한 메시지를 클라이언트에 전달
        """
        try:
            await self.send_json(event)
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason=str(e))

    @staticmethod
    def get_group_name(chatroom_id: int) -> str:
        # 채팅방 id를 사용하여 고유한 그룹 이름 구성
        return f"chat_{chatroom_id}"

    @staticmethod
    def decode_image(image_data: str) -> ContentFile[Any]:
        # Base64 문자열 디코딩
        format, imgstr = image_data.split(";base64,")
        ext = format.split("/")[-1]

        return ContentFile(base64.b64decode(imgstr), name="image." + ext)

    @database_sync_to_async  # type: ignore
    def get_chatroom(self, chatroom_id: int) -> Optional[Chatroom]:
        try:
            return Chatroom.objects.get(id=chatroom_id)
        except Chatroom.DoesNotExist:
            return None

    @database_sync_to_async  # type: ignore
    def save_chat_message(self, message: str, sender: Account, chatroom_id: int, **kwargs: Any) -> Message:
        return Message.objects.create(chatroom_id=chatroom_id, sender=sender, text=message, **kwargs)
