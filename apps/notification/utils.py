import logging
from typing import Any, Optional, Type

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import IntegrityError, models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_redis import get_redis_connection
from rest_framework.utils.serializer_helpers import ReturnDict

from apps.chat.consumers import ChatConsumer
from apps.chat.models import Chatroom, Message
from apps.chat.serializers import MessageSerializer
from apps.chat.utils import check_opponent_online
from apps.notification import serializers
from apps.notification.models import (
    GlobalNotification,
    GlobalNotificationConfirm,
    RentalNotification,
)
from apps.product.models import RentalHistory

channel_layer = get_channel_layer()
logger = logging.getLogger(__name__)
redis_conn = get_redis_connection("default")


@receiver(post_save, sender=GlobalNotification)  # type: ignore
def send_global_notification(sender, instance, created, **kwargs):
    """
    모든 유저에게 전송할 알림이 db에 저장되었을 때 그룹으로 알림을 발송해 줌
    """
    if created:
        group_name = "notification-global"
        data = serializers.GlobalNotificationSerializer(instance).data
        async_to_sync(channel_layer.group_send)(group_name, data)


@receiver(post_save, sender=Message)  # type: ignore
def new_chat_notification(sender, instance, created, **kwargs: Any):
    """
    새로운 채팅메시지가 생성되었을 때 상대방이 채팅 소켓에 접속중이지 않다면 알림을 보내줌
    """
    # 인스턴스가 저장되고 status가 True인 상태 -> 메시지가 생성되고 읽지 않은상태
    if created and instance.status is True:
        chat_group_name = ChatConsumer.get_group_name(instance.chatroom.id)
        notification_group = get_chat_notification_group_name(instance.chatroom.id)
        # 상대방이 채팅방에 접속중인지 확인하고 채팅방에 접속하지 않은 상태면 새메시지 알림을 전송
        if not check_opponent_online(chat_group_name):
            data = MessageSerializer(instance).data
            data["message"] = data.pop("text")
            data["type"] = "chat_notification"
            async_to_sync(channel_layer.group_send)(notification_group, data)


@receiver(post_save, sender=RentalHistory)  # type: ignore
def rental_notification(sender, instance, created, **kwargs: Any) -> None:
    """
    유저가 상품을 대여신청 했을 때 판매자에게 대여신청 알림을 보내주는 메서드
    """
    text = ""
    recipient_id = ""
    if created and instance.status == "REQUEST":
        text = f"{instance.borrower.nickname}님의 {instance.product.name} 상품 대여 신청 확인하기"
        recipient_id = instance.product.lender.id
    elif instance.status == "ACCEPT":
        text = f"{instance.product.name} 상품 대여 신청이 수락되었습니다."
        recipient_id = instance.borrower.id

    elif instance.status == "RETURNED":
        text = f"{instance.product.name}이 정상적으로 반납 완료되었습니다."
        recipient_id = instance.borrower.id

    elif instance.status == "BORROWING":
        text = f"{instance.product.name}의 대여가 시작되었습니다. 반납일은 {instance.return_data.date}입니다."
        recipient_id = instance.borrower.id

    chatroom_id = instance.product.chatroom_set.get(borrower=instance.borrower, lender=instance.product.lender).id
    # 가져온 채팅방 정보를 통해서 그룹네임을 가져옴
    chat_group_name = get_chat_notification_group_name(chatroom_id=chatroom_id)

    # 요청에 대한 새로운 알림을 데이터 베이스에 저장
    notification = create_rental_notification(
        model=RentalNotification, rental_history=instance, text=text, recipient_id=int(recipient_id)
    )
    # 저장된 알림을 직렬화해서 데이터에 담음
    serializer = serializers.RentalNotificationSerializer(notification)
    data = serializer.data
    # 직렬화된 데이터를 그룹으로 보냄
    async_to_sync(channel_layer.group_send)(chat_group_name, data)


def get_chat_notification_group_name(chatroom_id: int) -> str:
    return f"notification-chat_{chatroom_id}"


# def get_opponent_channel_name(group_name: str, channel_name: str) -> list[str]:
#     """django-redis를 사용해서 그룹에 속한 상대의 채널명을 가져옴"""
#     # 채널 레이어의 그룹 채널의 모든 값 가져오기
#     all_values = redis_conn.zrange(f"asgi:group:{group_name}", 0, -1)
#
#     # self.channel_name과 다른 값을 필터링하여 반환
#     other_values = [value.decode() for value in all_values if value.decode() != channel_name]
#
#     return other_values


def confirm_notification(model: models.Model, notification_id: int, user_id: int) -> None:
    """
    유저가 확인한 알림을 가져와서 comfirm = True 로 변경
    """
    if isinstance(model, RentalNotification):
        model.objects.filter(id=notification_id, recipient_id=user_id).update(confirm=True)
    if isinstance(model, GlobalNotificationConfirm):
        model.objects.filter(notification_id=notification_id, user_id=user_id).update(confirm=True)


def create_rental_notification(
    model: Type[RentalNotification],
    recipient_id: int,
    rental_history: RentalHistory,
    text: str,
    **kwargs: Any,
) -> Optional[RentalNotification]:
    try:
        return model.objects.create(recipient_id=recipient_id, rental_history=rental_history, text=text, **kwargs)
    except IntegrityError as e:
        logger.error("알림 db 저장 중 예외 발생: %s", e, exc_info=True)
        return None


def get_entered_chatroom_ids(user_id: int) -> Optional[list[int]]:
    try:
        # 해당 사용자가 판매자 또는 대여자인 모든 채팅방을 가져옴
        chatrooms = Chatroom.objects.filter(Q(borrower_id=user_id) | Q(lender_id=user_id))
        # 가져온 채팅방들의 아이디를 리스트로 반환
        chatroom_ids = chatrooms.values_list("id", flat=True)
        return chatroom_ids  # type: ignore
    except Chatroom.DoesNotExist:
        return None


def get_unread_chat_notifications(user_id: int) -> list[ReturnDict[Any, Any]]:
    # 해당 사용자가 판매자 또는 대여자인 모든 채팅방을 가져옴
    chatroom_list = Chatroom.objects.filter(Q(borrower_id=user_id) | Q(lender_id=user_id))
    # 각 채팅방의 최신 메시지를 필터링하여 가져옴
    unread_last_messages = []
    if chatroom_list:
        for chatroom in chatroom_list:
            message = chatroom.message_set.exclude(sender=user_id).filter(status=True).order_by("-timestamp").first()
            if message:
                data = MessageSerializer(message).data
                data["type"] = "chat_notification"
                unread_last_messages.append(data)
    return unread_last_messages


def get_unread_notifications(user_id: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    unread_global_notification = GlobalNotificationConfirm.objects.filter(user_id=user_id, confirm=False)
    if unread_global_notification:
        result["global_notification"] = serializers.GlobalNotificationConfirmSerializer(
            unread_global_notification, many=True
        ).data

    unread_rental_notification = RentalNotification.objects.filter(recipient_id=user_id, confirm=False)
    if unread_rental_notification:
        result["rental_notification"] = serializers.RentalNotificationSerializer(
            unread_rental_notification, many=True
        ).data

    unread_message = get_unread_chat_notifications(user_id=user_id)
    if unread_message:
        result["chat_notification"] = unread_message

    return result


def create_global_notification_confirm(user_id: int, notification_id: int) -> GlobalNotificationConfirm:
    obj, created = GlobalNotificationConfirm.objects.get_or_create(user_id=user_id, notification_id=notification_id)
    return obj
