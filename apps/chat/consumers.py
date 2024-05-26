import logging
from typing import Any, Optional

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.http import QueryDict
from django.utils import timezone
from django_redis import get_redis_connection

from apps.chat.models import Chatroom
from apps.chat.utils import (
    cashe_set_chat_message,
    check_entered_chatroom,
    check_opponent_online,
    get_group_name,
    save_redis_to_postgres,
    save_remaining_messages_to_postgres,
)
from apps.notification.utils import chat_notification
from apps.user.models import Account

logger = logging.getLogger(__name__)
redis_conn = get_redis_connection("default")


class ChatConsumer(AsyncJsonWebsocketConsumer):  # type: ignore
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.chat_group_name = ""
        self.chatroom_id = -1

    # 소켓에 연결
    async def connect(self) -> None:
        try:
            # scope로 채팅방 id 가져오기
            self.chatroom_id = self.scope["url_route"]["kwargs"]["chatroom_id"]
            self.chat_group_name = get_group_name(self.chatroom_id)

            chatroom = await self.get_chatroom(self.chatroom_id)

            if chatroom is None:
                raise ValueError("해당 채팅방이 존재하지 않습니다.")
            user = self.scope["user"]
            if not await database_sync_to_async(check_entered_chatroom)(chatroom, user):
                raise ValueError("해당 채팅방에 존재하는 유저가 아닙니다.")
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
        except ValueError as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1008, reason=str(e))
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
            text = content.get("text")
            image = content.get("image")
            sender = content.get("sender")

            # redis에 저장할 데이터
            data = {
                "text": text,
                "nickname": sender,
                "sender_id": self.scope["user"].id,
                "chatroom_id": self.chatroom_id,
                "status": True,
                "created_at": timezone.now().isoformat(),
            }

            # 수신한 데이터에서 이미지가 있으면 데이터에 포함
            if image:
                # image_data = self.decode_image(image)
                data["image"] = image

            # 만약 그룹에 속한 멤버가 2명이면 메시지는 무조건 읽은것으로 상태저장
            # django-redis를 사용해서 그룹에 속한 멤버의 수를 가져옴
            if check_opponent_online(self.chat_group_name):
                data["status"] = False

            # redis에 메시지를 캐싱해놓음
            cashe_set_chat_message(self.chat_group_name, data)
            # redis에 캐싱된 메시지가 100개가 넘으면 db로 저장하고 캐시를 비움
            if redis_conn.llen(f"{self.chat_group_name}_messages") > 100:
                await database_sync_to_async(save_redis_to_postgres)(self.chat_group_name)

            data["type"] = "chat_message"
            # 수신된 메시지와 정보를 그룹에 속한 채팅 참가자들에게 보내기
            await self.channel_layer.group_send(self.chat_group_name, data)
            # redis에 알림이 저장되고 상대가 채팅소켓에 접속중이지 않으면 읽지않은 채팅알림을 발송
            if data["status"]:
                await sync_to_async(chat_notification)(chatroom_id=self.chatroom_id, data=data)
        # 예외 발생 시 내용을 json으로 보내줌
        except ValueError as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1003, reason=str(e))
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason=str(e))

    # 소켓 연결 해제
    async def disconnect(self, close_code: int) -> None:
        # 레디스에 남은 메시지들을 데이터베이스에 저장
        if redis_conn.exists(f"{self.chat_group_name}_messages") and not check_opponent_online(self.chat_group_name):
            await database_sync_to_async(save_remaining_messages_to_postgres)(self.chat_group_name)
        # 레디스에 남은 그룹들 모두 해제
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)

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

    @database_sync_to_async  # type: ignore
    def get_chatroom(self, chatroom_id: int) -> Optional[Chatroom]:
        try:
            return Chatroom.objects.get(id=chatroom_id)
        except Chatroom.DoesNotExist:
            return None

    # @database_sync_to_async  # type: ignore
    # def save_chat_message(self, message: str, sender: Account, chatroom_id: int, **kwargs: Any) -> Message:
    #     return Message.objects.create(chatroom_id=chatroom_id, sender=sender, text=message, **kwargs)
