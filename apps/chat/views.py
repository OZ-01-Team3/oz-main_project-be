from typing import Any

from apps.chat import serializers
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import Alert, Chatroom, Message
from apps.chat.utils import (
    change_entered_status,
    check_entered_chatroom,
    delete_chatroom,
)


class ChatRoomView(APIView):
    @extend_schema(
        request=serializers.CreateChatroomSerializer,
        description="""
        빌리는 사람이 상품 게시자에게 채팅을 보내기 위해 채팅창을 열었을 때 채팅방을 개설하고 web socket으로 연결해주는 api
        """,
    )
    def post(self, request: Request) -> Response:
        serializer = serializers.CreateChatroomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(lender=request.user)
            return Response({"msg": "Successful Created Chatroom"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatDetailView(APIView):
    @extend_schema(
        responses=serializers.MessageSerializer,
        description="""
        채팅방에 해당하는 채팅 메시지를 내려주는 get 메서드
        """,
    )
    def get(self, request: Request, chatroom_id: int) -> Response:
        try:
            chatroom = Chatroom.objects.get(id=chatroom_id)
            if not check_entered_chatroom(chatroom=chatroom, user=request.user):
                return Response(
                    {"msg": "이미 나간 채팅방이거나 접근할 수 없는 채팅방입니다."}, status=status.HTTP_400_BAD_REQUEST
                )
            messages = Message.objects.filter(chatroom=chatroom)
            serializer = serializers.MessageSerializer(messages, many=True)
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