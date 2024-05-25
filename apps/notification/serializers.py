from typing import Any, Optional

from rest_framework import serializers

from apps.notification.models import (
    GlobalNotification,
    GlobalNotificationConfirm,
    RentalNotification,
)


class GlobalNotificationSerializer(serializers.ModelSerializer[GlobalNotification]):
    class Meta:
        model = GlobalNotification
        exclude = ["updated_at"]

    def to_representation(self, instance: GlobalNotification) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["type"] = "global_notification"
        return data


class GlobalNotificationConfirmSerializer(serializers.ModelSerializer[GlobalNotificationConfirm]):
    text = serializers.CharField(source="notification.text", read_only=True)
    image = serializers.SerializerMethodField()
    recipient = serializers.CharField(source="notification.user", read_only=True)

    class Meta:
        model = GlobalNotificationConfirm
        exclude = ["updated_at", "notification", "user"]

    def get_image(self, obj: GlobalNotificationConfirm) -> Optional[str]:
        if obj.notification.image:
            return str(obj.notification.image.url)
        return None

    def to_representation(self, instance: GlobalNotificationConfirm) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["type"] = "global_notification"
        return data


class RentalNotificationSerializer(serializers.ModelSerializer[RentalNotification]):
    product_name = serializers.CharField(source="rental_history.product.name")  # 상품 이름
    image = serializers.SerializerMethodField()  # 상품 이미지
    borrower = serializers.CharField(source="rental_history.borrower.nickname")  # 빌리는 사람
    lender = serializers.CharField(source="rental_history.product.lender.nickname")  # 판매자
    rental_date = serializers.DateTimeField(source="rental_history.rental_date")  # 대여일
    return_date = serializers.DateTimeField(source="rental_history.return_date")  # 반납일
    status = serializers.CharField(source="rental_history.status")  # 상태 : 대여신청, 대여수락, 대여중, 반납

    class Meta:
        model = RentalNotification
        fields = [
            "id",
            "recipient",
            "product_name",
            "image",
            "borrower",
            "lender",
            "rental_date",
            "return_date",
            "status",
            "created_at",
            "text",
        ]

    def get_image(self, obj: RentalNotification) -> Any:
        product_images: RentalNotification = obj.rental_history.product.images.first()  # type: ignore
        if product_images:
            # 이미지의 URL을 리턴
            return product_images.image.url  # type: ignore
        return None  # 이미지가 없을 경우 None을 리턴

    def to_representation(self, instance: RentalNotification) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["type"] = "rental_notification"
        return data
