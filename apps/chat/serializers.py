from typing import Any, Dict

from django.db.models import Q
from rest_framework import serializers

from apps.chat.models import Chatroom, Message
from apps.product.models import ProductImage


class ChatroomListSerializer(serializers.ModelSerializer[Chatroom]):
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

        last_message = Message.objects.filter(chatroom=instance).order_by("-timestamp").first()
        if last_message:
            data["last_message"] = MessageSerializer(last_message).data
        return data


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
    product_rental_fee = serializers.CharField(source="product.rental_fee", read_only=True)
    product_condition = serializers.CharField(source="product.condition", read_only=True)

    class Meta:
        model = Chatroom
        fields = ["product", "product_image", "product_name", "product_rental_fee", "product_condition"]

    def to_representation(self, instance: Chatroom) -> Dict[str, Any]:
        data = super().to_representation(instance)
        user = self.context.get("user")
        messages = Message.objects.filter(~Q(sender=user), chatroom=instance)

        if messages:
            # bulk_update 메서드를 사용하여 한 번에 여러 개체를 업데이트, 안읽은 메시지들을 읽음처리
            filter_condition = Q(status=True, id__in=messages.values_list("id", flat=True))
            Message.objects.filter(filter_condition).update(status=False)
            # 업데이트된 메시지를 다시 가져와서 시리얼라이저로 직렬화
        messages = Message.objects.filter(chatroom=instance).order_by("timestamp")
        serializer = MessageSerializer(messages, many=True)
        data["messages"] = serializer.data

        return data

    def get_product_image(self, obj):
        if obj.product:
            product_images = obj.product.productimage_set.first()
            if product_images:
                return product_images.image.url  # 이미지의 URL을 리턴
        return None  # 이미지가 없을 경우 None을 리턴
