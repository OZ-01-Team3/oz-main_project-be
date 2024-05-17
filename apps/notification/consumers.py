import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.notification.models import GlobalNotification, GlobalNotificationConfirm
from apps.notification.utils import (
    confirm_notification,
    create_global_notification_confirm,
    get_chat_notification_group_name,
    get_entered_chatroom_ids,
    get_unread_notifications,
)

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    groups = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = ""

    async def connect(self) -> None:
        try:
            self.user = self.scope["user"]

            # 모든 유저에게 알림을 전달하는 그룹 추가
            global_group_name = "notification-global"
            self.groups.append(global_group_name)
            # 각 채팅방에 대한 알림을 전달하는 그룹 추가
            await self.group_add_by_chatroom_ids(user_id=self.user.id)
            # 채널레이어에 각 알림 그룹들을 group_add 로 추가
            for group in self.groups:
                await self.channel_layer.group_add(group, self.channel_name)

            # 그룹 추가가 정상적으로 완료되면 소켓 연결 수락
            await self.accept()

            # 소켓 연결이 완료되고 읽지 않은 알림이 있다면 가져와서 보내주기
            unread_notifications = await database_sync_to_async(get_unread_notifications)(user_id=self.user.id)
            if unread_notifications:
                await self.send_json(unread_notifications)
        except Exception as e:
            # 소켓 연결 실패 또는 예외 발생시 소켓 연결을 종료하고 그룹 삭제
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(code=1011, reason=str(e))

    async def disconnect(self, close_code: int):
        # 모든 그룹 연결 해제
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, content: dict[str, Any], **kwargs: Any) -> None:
        if content["command"]:
            await self.commands[content["command"]](self, data=content)

    async def global_notification_confirm(self, data: dict[str, Any]) -> None:
        try:
            await database_sync_to_async(confirm_notification)(
                model=GlobalNotificationConfirm, user_id=self.user.id, notification_id=data["notification_id"]
            )
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(1011, reason="알림 읽음 처리시 예외 발생")

    async def rental_notification_confirm(self, data: dict[str, Any]) -> None:
        try:
            await database_sync_to_async(confirm_notification)(
                model=GlobalNotification, user_id=self.user.id, notification_id=data["notification_id"]
            )
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(1011, reason="알림 읽음 처리시 예외 발생")

    async def notification_chat(self, event: dict[str, Any]) -> None:
        try:
            if event["nickname"] != self.user.nickname:
                await self.send_json(event)
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(1011, reason="클라이언트로 알림 전송 중 예외 발생")

    async def notification_rental(self, event: dict[str, Any]) -> None:
        try:
            if event["recipient"] == self.user.id:
                await self.send_json(event)
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(1011, reason="클라이언트로 알림 전송 중 예외 발생")

    async def notification_global(self, event: dict[str, Any]) -> None:
        try:
            # 알림을 보내기전에 각 유저마다 알림을 읽었는지 확인할 수 있는 fk 모델 생성
            await database_sync_to_async(create_global_notification_confirm)(
                user_id=self.user.id, notification_id=event["id"]
            )
            # 알림을 클라이언트로 전송
            await self.send_json(event)
        except Exception as e:
            logger.error("예외 발생: %s", e, exc_info=True)
            await self.close(1011, reason="클라이언트로 알림 전송 중 예외 발생")

    @database_sync_to_async
    def group_add_by_chatroom_ids(self, user_id: int) -> None:
        entered_chatroom_ids = get_entered_chatroom_ids(user_id=user_id)
        for chatroom_id in entered_chatroom_ids:
            chat_notification_group = get_chat_notification_group_name(chatroom_id=chatroom_id)
            self.groups.append(chat_notification_group)

    commands = {
        "notification.rental.confirm": rental_notification_confirm,
        "notification.global.confirm": global_notification_confirm,
    }
