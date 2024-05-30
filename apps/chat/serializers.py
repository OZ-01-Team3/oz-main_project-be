from typing import Any, Dict, Optional

from django.db.models import Q
from rest_framework import serializers

from apps.chat.models import Chatroom, Message
from apps.chat.utils import (
    get_chatroom_message,
    get_last_message,
    get_unread_message_count_at_redis,
    read_messages_at_postgres,
    read_messages_at_redis,
)
from apps.product.models import ProductImage


class ChatroomListSerializer(serializers.ModelSerializer[Chatroom]):
    unread_chat_count = serializers.SerializerMethodField()  # 안읽은 채팅 수

    class Meta:
        model = Chatroom
        exclude = ["borrower", "lender", "borrower_status", "lender_status"]

    def to_representation(self, instance: Chatroom) -> Dict[str, Any]:
        data = super().to_representation(instance)
        user = self.context.get("user")
        if user == instance.lender:
            user_data = {
                "nickname": instance.borrower.nickname,
            }
            if instance.borrower.profile_img:
                user_data["profile_img"] = instance.borrower.profile_img.url
            data["user_info"] = user_data

        if user == instance.borrower:
            user_data = {
                "nickname": instance.lender.nickname,
            }
            if instance.lender.profile_img:
                user_data["profile_img"] = instance.lender.profile_img.url
            data["user_info"] = user_data

        if instance.product:
            product_image = ProductImage.objects.filter(product=instance.product).first()
            if product_image:
                data["product_image"] = product_image.image.url

        last_message = get_last_message(chatroom_id=instance.id)
        data["last_message"] = last_message
        return data

    def get_unread_chat_count(self, obj: Chatroom) -> Optional[int]:
        user = self.context.get("user")
        if user and obj.message_set:
            user = self.context.get("user")
            db_unread_count: int = obj.message_set.filter(~Q(sender=user), status=True).count()
            redis_unread_count: int = get_unread_message_count_at_redis(chatroom_id=obj.id, nickname=user.nickname)
            return db_unread_count + redis_unread_count
        return None


class CreateChatroomSerializer(serializers.ModelSerializer[Chatroom]):
    class Meta:
        model = Chatroom
        fields = "__all__"
        read_only_fields = ["borrower", "borrower_status", "lender_status"]


class MessageSerializer(serializers.ModelSerializer[Message]):
    nickname = serializers.CharField(source="sender.nickname", read_only=True)

    class Meta:
        model = Message
        exclude = ["sender"]


class EnterChatroomSerializer(serializers.ModelSerializer[Chatroom]):
    product_image = serializers.SerializerMethodField()  # 상품 이미지
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_rental_fee = serializers.IntegerField(source="product.rental_fee", read_only=True)
    product_condition = serializers.CharField(source="product.condition", read_only=True)

    class Meta:
        model = Chatroom
        fields = ["product", "product_image", "product_name", "product_rental_fee", "product_condition"]

    def to_representation(self, instance: Chatroom) -> Dict[str, Any]:
        data = super().to_representation(instance)
        user = self.context.get("user")
        if user:
            # redis에 캐싱된 채팅방 메시지 읽음처리
            read_messages_at_redis(nickname=user.nickname, chatroom_id=instance.id)
            # postgres에 저장된 채팅방 메시지를 읽음처리
            read_messages_at_postgres(user_id=user.id, chatroom_id=instance.id)

            messages = get_chatroom_message(chatroom_id=instance.id)
            data["messages"] = messages
        return data

    def get_product_image(self, obj: ProductImage) -> Any:
        if obj.product:
            product_images = obj.product.images.first()
            if product_images:
                return product_images.image.url  # 이미지의 URL을 리턴
        return None  # 이미지가 없을 경우 None을 리턴
