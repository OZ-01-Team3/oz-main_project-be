from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as serializer
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat import serializers
from apps.chat.models import Chatroom, Message
from apps.chat.utils import (
    change_entered_status,
    check_entered_chatroom,
    delete_chatroom,
)
from apps.user.api_schema import UserInfoSerializer


def render_chat(request: HttpRequest) -> HttpResponse:
    return render(request, "chat_test.html")


class ChatRoomView(APIView):
    @extend_schema(
        responses=inline_serializer(
            name="ChatRoomSerializer",
            fields={
                "id": serializer.IntegerField(),
                "product": serializer.UUIDField(),
                "product_image": serializer.URLField(),
                "last_message": serializer.CharField(),
                "unread_chat_count": serializer.IntegerField(),
                "user_info": UserInfoSerializer(),
            },
            many=True,
        ),
        description="유저가 참여한 채팅방 리스트를 내려주는 get메서드",
    )
    def get(self, request: Request) -> Response:
        chatroom_list = Chatroom.objects.filter(
            Q(lender=request.user, lender_status=True) | Q(borrower=request.user, borrower_status=True)
        )
        if chatroom_list:
            serializer = serializers.ChatroomListSerializer(chatroom_list, context={"user": request.user}, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"msg": "참여 중인 채팅방을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=serializers.CreateChatroomSerializer,
        description="""
        빌리는 사람이 상품 게시자에게 채팅을 보내기 위해 채팅창을 열었을 때 채팅방을 개설하고 web socket으로 연결해주는 api
        """,
    )
    def post(self, request: Request) -> Response:
        if isinstance(request.user, AnonymousUser):
            return Response({"msg": "유저 자격증명이 불일치 합니다. 재로그인이 필요합니다."})
        product_uuid = request.data.get("product")
        lender_id = request.data.get("lender")
        if Chatroom.objects.filter(
            product=product_uuid,
            borrower_id=request.user.id,
            lender_id=lender_id,
            lender_status=True,
            borrower_status=True,
        ).exists():
            return Response({"msg": "이미 개설된 채팅방 내역이 존재합니다."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = serializers.CreateChatroomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(borrower=request.user)
            return Response({"msg": "Successful Created Chatroom"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatDetailView(APIView):
    @extend_schema(
        responses=inline_serializer(
            name="inline_serializer",
            fields={
                "product_image": serializer.CharField(),
                "product_name": serializer.CharField(),
                "product_rental_fee": serializer.CharField(),
                "product_condition": serializer.CharField(),
                "messages": serializers.MessageSerializer(many=True),
            },
        ),
        description="""
            채팅방에 입장시 채팅방의 메시지를 내려주고, 상품에 대한 정보를 내려줌
            """,
    )
    def get(self, request: Request, chatroom_id: int) -> Response:
        try:
            chatroom = Chatroom.objects.get(id=chatroom_id)
            if not check_entered_chatroom(chatroom=chatroom, user=request.user):
                return Response(
                    {"msg": "이미 나간 채팅방이거나 접근할 수 없는 채팅방입니다."}, status=status.HTTP_400_BAD_REQUEST
                )
            serializer = serializers.EnterChatroomSerializer(chatroom, context={"user": request.user})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Chatroom.DoesNotExist:
            return Response({"msg": "해당 채팅방이 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        description="""
        유저가 채팅방 나가기를 시도했을 때
        if. 채팅방에 남은 유저가 있으면> -> 유저의 나가기 상태만 변경, 채팅방 유지
        if. 남은 유저가 없다면? -> 채팅방 삭제
        """
    )
    @transaction.atomic
    def delete(self, request: Request, chatroom_id: int) -> Response:
        try:
            chatroom = Chatroom.objects.get(id=chatroom_id)
            if not check_entered_chatroom(chatroom=chatroom, user=request.user):
                return Response(
                    {"msg": "이미 나간 채팅방이거나 접근할 수 없는 채팅방입니다."}, status=status.HTTP_400_BAD_REQUEST
                )
            if delete_chatroom(chatroom=chatroom):
                return Response(
                    {"msg": "채팅방에 남은 유저가 없어 채팅방이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
                )
            change_entered_status(chatroom=chatroom, user=request.user)
            return Response({"msg": "채팅방 나가기에 성공했습니다."}, status=status.HTTP_200_OK)
        except Chatroom.DoesNotExist:
            return Response({"msg": "해당 채팅방이 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
