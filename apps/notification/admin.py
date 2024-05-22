from typing import Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.notification import serializers
from apps.notification.models import (
    GlobalNotification,
    GlobalNotificationConfirm,
    RentalNotification,
)
from apps.user.models import Account


@admin.register(GlobalNotification)
class GlobalNotificationAdmin(admin.ModelAdmin[GlobalNotification]):
    fieldsets = (("Image", {"fields": ("image",)}), ("Text", {"fields": ("text",)}))
    list_display = ("id", "text", "image_url", "updated_at", "created_at")
    search_fields = ("text",)

    class GlobalNotificationConfirmInline(admin.StackedInline[GlobalNotificationConfirm, GlobalNotification]):
        model = GlobalNotificationConfirm
        extra = 10
        can_delete = True
        show_change_link = True
        classes = ("collapse",)

    inlines = [GlobalNotificationConfirmInline]

    actions = ["send_notification_to_all_users"]

    def image_url(self, obj: GlobalNotification) -> Optional[str]:
        if obj.image:
            return str(obj.image.url)
        return None

    def send_notification_to_all_users(self, request: HttpRequest, queryset: QuerySet[GlobalNotification]) -> None:
        notifications = list(queryset)
        users = Account.objects.all()
        confirm_objects = []
        for notification in notifications:
            confirm_objects.extend([GlobalNotificationConfirm(user=user, notification=notification) for user in users])

        GlobalNotificationConfirm.objects.bulk_create(confirm_objects)

        channel_layer = get_channel_layer()
        group_name = "notification-global"

        for notification in notifications:
            data = serializers.GlobalNotificationSerializer(notification).data
            data["type"] = "notification_global"
            async_to_sync(channel_layer.group_send)(group_name, data)

    send_notification_to_all_users.short_description = "모든 유저에게 선택한 알림 전송하기"  # type: ignore


@admin.register(GlobalNotificationConfirm)
class GlobalNotificationConfirmAdmin(admin.ModelAdmin[GlobalNotificationConfirm]):
    fieldsets = (
        ("Notification", {"fields": ("notification",)}),
        ("User", {"fields": ("user",)}),
        ("ConfirmState", {"fields": ("confirm",)}),
    )
    list_display = ("id", "notification", "user", "confirm")
    search_fields = ("notification", "user")
    list_filter = ("notification", "user")
    actions = ["confirm_notification"]

    def confirm_notification(self, request: HttpRequest, queryset: QuerySet[GlobalNotificationConfirm]) -> None:
        if queryset.exists():
            confirm_objects = list(queryset)
            for obj in confirm_objects:
                obj.confirm = True
            GlobalNotificationConfirm.objects.bulk_update(confirm_objects, ("confirm",))

    confirm_notification.short_description = "선택한 객체의 알림 확인상태로 변경"  # type: ignore


@admin.register(RentalNotification)
class RentalNotificationAdmin(admin.ModelAdmin[RentalNotification]):
    fieldsets = (
        ("Recipient", {"fields": ("recipient",)}),
        ("Rental_Info", {"fields": ("rental_history",)}),
        ("Notification_Info", {"fields": ("text",)}),
        ("Confirm_State", {"fields": ("confirm",)}),
    )
    list_display = ("id", "product_name", "recipient", "rental_history", "text", "confirm")
    list_filter = ("recipient", "rental_history")
    search_fields = ("text", "product_name")

    actions = ["notification_confirm"]

    def product_name(self, obj: RentalNotification) -> Optional[str]:
        if obj.rental_history:
            product_name = obj.rental_history.product.name
            return product_name
        return None

    def notification_confirm(self, request: HttpRequest, queryset: QuerySet[RentalNotification]) -> None:
        if queryset.exists():
            notifications = list(queryset)
            for obj in notifications:
                obj.confirm = True

            RentalNotification.objects.bulk_update(notifications, ("confirm",))

    notification_confirm.short_description = "선택한 알림 확인 상태로 변경하기"  # type: ignore
