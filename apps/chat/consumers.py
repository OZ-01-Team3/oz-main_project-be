import base64
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.files.base import ContentFile
from django.http import QueryDict

from apps.chat.models import Alert, Chatroom, Message
from apps.chat.serializers import MessageSerializer
from apps.chat.utils import check_entered_chatroom
from apps.user.models import Account

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):  # type: ignore
    # 소켓에 연결
    async def connect(self) -> None:
        try:
            # scope로 채팅방 id 가져오기
            self.chatroom_id = self.scope["url_route"]["kwargs"]["chatroom_id"]
            self.chat_group_name = self.get_group_name(self.chatroom_id)

            if not await self.check_room_exists(self.chatroom_id):
                await self.close(code=1008, reason="해당 채팅방이 존재하지 않습니다.")
            self.user = self.scope["user"]
            chatroom = await database_sync_to_async(Chatroom.objects.get)(id=self.chatroom_id)
            if not await database_sync_to_async(check_entered_chatroom)(chatroom, self.user):
                await self.close(code=1008, reason="해당 채팅방에 존재하는 유저가 아닙니다.")
            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason=str(e))

    async def receive_json(self, content: QueryDict) -> None:
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
            chat = await self.save_chat_message(**data)

            # 저장된 메시지를 직렬화
            serializer = MessageSerializer(chat)

            # 수신된 메시지와 정보를 그룹에 속한 채팅 참가자들에게 보내기
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    "message_id": serializer.data.get("id"),
                    "type": "chat_message",
                    "message": serializer.data.get("text"),
                    "nickname": serializer.data.get("nickname"),
                    "image_url": serializer.data.get("image"),
                },
            )
        # 예외 발생 시 내용을 json으로 보내줌
        except ValueError as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1003, reason=str(e))
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason=str(e))

    # 소켓 연결 해제
    async def disconnect(self, close_code: int) -> None:
        chat_group_name = self.get_group_name(self.chatroom_id)
        await self.channel_layer.group_discard(chat_group_name, self.channel_name)

    async def chat_message(self, event: QueryDict) -> None:
        """
        그룹으로부터 수신한 메시지를 클라이언트에 전달
        """
        try:
            message_id = event.get("message_id")
            message = event.get("message")
            nickname = event.get("nickname")
            image_url = event.get("image_url")

            # 만약 메시지 sender와 수신자의 id가 다르다면 메시지 읽음처리
            message_obj = await self.update_message_status(message_id, self.scope["user"].id)

            await self.send_json(
                {
                    "type": "chat_message",
                    "message": message,
                    "nickname": nickname,
                    "image_url": image_url,
                    "status": message_obj.status,  # 읽음 처리 된 상태를 반환
                }
            )
        except Message.DoesNotExist as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason="메시지 읽음 처리 실패")
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
    def get_user(self, **kwarg: Any) -> Account:
        try:
            return Account.objects.get(**kwarg)
        except Account.DoesNotExist:
            raise ValueError("해당 유저를 찾을 수 없습니다.")

    @database_sync_to_async  # type: ignore
    def check_room_exists(self, chatroom_id: int) -> bool:
        # 주어진 ID로 채팅방이 존재하는지 확인합니다.
        return Chatroom.objects.filter(id=chatroom_id).exists()

    @database_sync_to_async  # type: ignore
    def create_alert_leave_chatroom(self) -> Alert:
        return Alert.objects.create(chatroom_id=self.chatroom_id, text="상대방이 채팅에서 나갔습니다.")

    @database_sync_to_async  # type: ignore
    def save_chat_message(self, message: str, sender: Account, chatroom_id: int, **kwargs: Any) -> Message:
        return Message.objects.create(chatroom_id=chatroom_id, sender=sender, text=message, **kwargs)

    @database_sync_to_async  # type: ignore
    def update_message_status(self, message_id: int, user_id: int) -> Message:
        message = Message.objects.get(id=message_id)
        if message.sender_id != user_id:
            message.status = False
            message.save()
            message.refresh_from_db()
            return message
        return message
