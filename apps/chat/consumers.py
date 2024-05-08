import base64
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.files.base import ContentFile
from apps.user.models import Account
from apps.chat.models import Message, Chatroom, Alert

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    # 소켓에 연결
    async def connect(self):
        try:
            # scope로 채팅방 id 가져오기
            self.chatroom_id = self.scope['url_route']['kwargs']['chatroom_id']
            self.chat_group_name = self.get_group_name(self.chatroom_id)

            if not await self.check_room_exists(self.chatroom_id):
                raise ValueError('해당 채팅방이 존재하지 않습니다.')

            await self.channel_layer.group_add(
                self.chat_group_name,
                self.channel_name
            )
            await self.accept()

        except (KeyError, ValueError) as e:
            # chatroom_id를 가져오지 못하거나 해당 채팅방이 존재하지않으면 에러 메시지를 보내고 연결 해제
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.send_json({"error": str(e)})
            await self.close()

    async def receive_json(self, content):
        """
        서버에서 메시지 받고 데이터 서버에 저장,
        그룹 접속자에게 메시지를 전달
        """
        try:
            # 수신된 JSON에서 필요한 데이터를 가져옴
            message = content.get('message')
            sender_email = content.get('sender_email')
            image = content.get('image')
            # 이메일로 유저를 가져옴
            sender = await self.get_user(email=sender_email)

            if image:
                image_data = self.decode_image(image)
            # 메시지를 데이터 베이스에 저장함
            chat = await self.save_chat_message(
                message=message, sender=sender, image=image_data, chatroom_id=self.chatroom_id
            )
            from apps.chat.serializers import MessageSerializer

            serializer = MessageSerializer(chat)
            # 수신된 메시지와 정보를 그룹에 속한 채팅 참가자들에게 보내기
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message': serializer.data.get('text'),
                    'sender_email': serializer.data.get('sender_nickname'),
                    'image_url': serializer.data.get('image'),
                }
            )
        # 예외 발생 시 내용을 json으로 보내줌
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.send_json({"error": str(e)})

    # 소켓 연결 해제
    async def disconnect(self, close_code):
        chat_group_name = self.get_group_name(self.chatroom_id)
        await self.channel_layer.group_discard(chat_group_name, self.channel_name)

    async def chat_message(self, event):
        """
        그룹으로부터 수신한 메시지를 클라이언트에 전달
        """
        try:
            message = event.get("message")
            sender_email = event.get("sender_email")
            image_url = event.get("image_url")

            await self.send_json(
                {"type": "chat_message", "message": message, "sender_email": sender_email, "image_url": image_url}
            )
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.send_json({"error": "메시지 전송 실패"})

    @staticmethod
    def get_group_name(chatroom_id):
        # 채팅방 id를 사용하여 고유한 그룹 이름 구성
        return f"chat_{chatroom_id}"

    @staticmethod
    def decode_image(image_data):
        # Base64 문자열 디코딩
        format, imgstr = image_data.split(";base64,")
        ext = format.split("/")[-1]
        image_data = ContentFile(base64.b64decode(imgstr), name="image." + ext)

        return image_data

    @database_sync_to_async
    def get_user(self, **kwarg: any):
        try:
            return Account.objects.get(**kwarg)
        except Account.DoesNotExist:
            raise ValueError("해당 유저를 찾을 수 없습니다.")

    @database_sync_to_async
    def check_room_exists(self, chatroom_id: int):
        # 주어진 ID로 채팅방이 존재하는지 확인합니다.
        return Chatroom.objects.filter(id=chatroom_id).exists()

    @database_sync_to_async
    def create_alert_leave_chatroom(self):
        return Alert.objects.create(chatroom_id=self.chatroom_id, text="상대방이 채팅에서 나갔습니다.")

    @database_sync_to_async
    def save_chat_message(self, message: str, sender: str, chatroom_id: int, image):
        return Message.objects.create(chatroom_id=chatroom_id, sender=sender, text=message, image=image)
