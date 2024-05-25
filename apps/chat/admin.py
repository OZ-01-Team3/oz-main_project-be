from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.chat.models import Chatroom, Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin[Message]):
    # add or modify fieldsets
    fieldsets = (
        ("Sender", {"fields": ("sender",)}),
        (
            "MessageInfo",
            {
                "fields": (
                    "chatroom",
                    "text",
                    "image",
                )
            },
        ),
        ("Status", {"fields": ("status",)}),
    )

    list_display = ("chatroom", "sender", "text", "image", "status", "updated_at", "created_at")
    search_fields = ("text", "sender")
    ordering = ("sender",)

    actions = ["set_status_false", "set_status_true"]

    def set_status_false(self, request: HttpRequest, queryset: QuerySet[Message]) -> None:
        if queryset.exists():
            # 쿼리셋의 객체들을 리스트화
            messages = list(queryset)
            # 각 객체의 읽음 여부를 업데이트.
            for message in messages:
                message.status = False
            # 벌크 업데이트로 하나의 쿼리로 업데이트
            Message.objects.bulk_update(messages, ["status"])

    def set_status_true(self, request: HttpRequest, queryset: QuerySet[Message]) -> None:
        if queryset.exists():
            # 쿼리셋의 객체들을 리스트화
            messages = list(queryset)
            # 각 객체의 읽음 여부를 업데이트.
            for message in messages:
                message.status = True
            # 벌크 업데이트로 하나의 쿼리로 업데이트
            Message.objects.bulk_update(messages, ["status"])

    set_status_false.short_description = "선택한 메시지를 읽음으로 처리"  # type: ignore
    set_status_true.short_description = "선택한 메시지를 안읽음으로 처리"  # type: ignore


@admin.register(Chatroom)
class ChatroomAdmin(admin.ModelAdmin[Chatroom]):
    fieldsets = (
        ("About", {"fields": ("product",)}),
        ("UserInfo", {"fields": ("borrower", "lender")}),
        ("LeaveInfo", {"fields": ("borrower_status", "lender_status")}),
    )
    list_display = ("id", "product", "borrower", "lender", "borrower_status", "lender_status")
    search_fields = ("product", "borrower", "lender")
    list_filter = ("product",)
    ordering = ("id",)

    actions = ["leave_borrower", "leave_lender"]

    class MessageInline(admin.StackedInline[Message, Chatroom]):
        model = Message

    inlines = [MessageInline]

    # 선택한 채팅방의 구매자가 나가게하는 액션
    def leave_borrower(self, request: HttpRequest, queryset: QuerySet[Chatroom]) -> None:
        if queryset.exists():
            chatrooms = list(queryset)
            to_delete = []

            for chatroom in chatrooms:
                if not chatroom.lender_status:
                    to_delete.append(chatroom)
                else:
                    chatroom.borrower_status = False

            # 삭제할 객체들을 삭제
            for chatroom in to_delete:
                chatroom.delete()
                chatrooms.remove(chatroom)

            # 남아 있는 객체들을 업데이트
            if chatrooms:
                Chatroom.objects.bulk_update(chatrooms, ["borrower_status"])

    def leave_lender(self, request: HttpRequest, queryset: QuerySet[Chatroom]) -> None:
        if queryset.exists():
            chatrooms = list(queryset)
            to_delete = []

            for chatroom in chatrooms:
                if not chatroom.borrower_status:
                    to_delete.append(chatroom)
                else:
                    chatroom.lender_status = False

            for chatroom in to_delete:
                chatroom.delete()
                chatrooms.remove(chatroom)

            if chatrooms:
                Chatroom.objects.bulk_update(chatrooms, ["lender_status"])

    leave_lender.short_description = "선택한 채팅방에서 판매자가 나가기"  # type: ignore
    leave_borrower.short_description = "선택한 채팅방에서 대여자가 나가기"  # type: ignore
