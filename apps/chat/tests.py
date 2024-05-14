from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from django.urls import path, reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.category.models import Category
from apps.chat.consumers import ChatConsumer
from apps.chat.models import Chatroom, Message
from apps.product.models import Product
from apps.user.models import Account


class ChatRoomTestCase(APITestCase):
    def setUp(self) -> None:
        # 요청을 보낼 유저 생성
        self.user = Account.objects.create_user(email="test@example.com", password="testpw123", nickname="test1")
        # 대여 상품 판매자 생성
        self.lender = Account.objects.create_user(email="test2s@example.com", password="testpw1234", nickname="test2")
        # 대여 상품 생성
        self.category = Category.objects.create(name="test")
        self.product = Product.objects.create(
            name="Test Product",
            lender=self.lender,
            product_category=self.category,
            condition="Test Condition",
            purchasing_price=60000,
            rental_fee=5000,
            size="XL",
        )
        self.client.force_login(user=self.user)

    def test_정상적인_채팅방_만들기_요청(self) -> None:
        url = reverse("chatroom")
        data = {"lender": self.lender.id}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chatroom.objects.count(), 1)
        self.assertEqual(response.data.get("msg"), "Successful Created Chatroom")

    def test_잘못된_lender의_아이디로_채팅방을_개설하려는_경우(self) -> None:
        url = reverse("chatroom")
        data = {"lender": 13241}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Chatroom.objects.count(), 0)

    def test_로그인_유저의_채팅방리스트_가져오기(self) -> None:
        url = reverse("chatroom")
        # 먼저 채팅방 만들기
        chatroom = Chatroom.objects.create(lender=self.lender, borrower=self.user, product=self.product)
        last_message = Message.objects.create(sender=self.user, text="test_last_message", chatroom=chatroom)
        # 채팅방 리스트 가져오기
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0].get("id"), chatroom.id)
        self.assertEqual(response.data[0]["user_info"].get("nickname"), chatroom.lender.nickname)
        self.assertEqual(response.data[0]["last_message"].get("text"), last_message.text)
        self.assertEqual(response.data[0]["last_message"].get("nickname"), last_message.sender.nickname)


class ChatDetailTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = Account.objects.create_user(email="test@example.com", password="testpw1234", nickname="test1")
        self.lender = Account.objects.create_user(email="test2@example.com", password="testpw1234", nickname="test2")
        self.chatroom = Chatroom.objects.create(borrower=self.user, lender=self.lender)
        for i in range(10):
            Message.objects.create(chatroom=self.chatroom, sender=self.user, text=f"test-message-{i}")
            Message.objects.create(chatroom=self.chatroom, sender=self.lender, text=f"test-message-{i}")
        self.client.force_login(user=self.user)

    def test_채팅에_참여한_유저가_get요청을_보내는_경우(self) -> None:
        url = reverse("chat-detail", kwargs={"chatroom_id": self.chatroom.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.chatroom.message_set.count(), len(response.data.get("messages")))

    def test_비정상적인_유저가_get요청을_보내는_경우(self) -> None:
        invaild_user = Account.objects.create_user(email="invalid-user@example.com", password="testpassword123")
        self.client.logout()
        self.client.force_login(invaild_user)

        url = reverse("chat-detail", kwargs={"chatroom_id": self.chatroom.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("msg"), "이미 나간 채팅방이거나 접근할 수 없는 채팅방입니다.")

    def test_유효하지않은_채팅방ID로_get요청을_보내는_경우(self) -> None:
        url = reverse("chat-detail", kwargs={"chatroom_id": 123112314})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get("msg"), "해당 채팅방이 존재하지 않습니다.")

    def test_채팅방에서_한명만_나갈때_delete요청을_보내는_경우(self) -> None:
        url = reverse("chat-detail", kwargs={"chatroom_id": self.chatroom.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("msg"), "채팅방 나가기에 성공했습니다.")

    def test_채팅방에서_한명이_나간상태에서_delete요청을_보내는_경우(self) -> None:
        url = reverse("chat-detail", kwargs={"chatroom_id": self.chatroom.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("msg"), "채팅방 나가기에 성공했습니다.")

        self.client.logout()
        self.client.force_login(self.lender)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data.get("msg"), "채팅방에 남은 유저가 없어 채팅방이 삭제되었습니다.")

    def test_비정상적인_유저가_delete요청을_보내는_경우(self) -> None:
        invaild_user = Account.objects.create_user(email="invalid-user@example.com", password="testpassword123")
        self.client.logout()
        self.client.force_login(invaild_user)

        url = reverse("chat-detail", kwargs={"chatroom_id": self.chatroom.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("msg"), "이미 나간 채팅방이거나 접근할 수 없는 채팅방입니다.")

    def test_유효하지않은_채팅방ID로_delete요청을_보내는_경우(self) -> None:
        url = reverse("chat-detail", kwargs={"chatroom_id": 123112314})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get("msg"), "해당 채팅방이 존재하지 않습니다.")


class ChatConsumerTest(TransactionTestCase):
    def setUp(self) -> None:
        # 요청을 보낼 유저 생성
        self.user = Account.objects.create_user(email="test@example.com", password="testpw123", nickname="test1")
        # 대여 상품 판매자 생성
        self.user2 = Account.objects.create_user(email="test2s@example.com", password="testpw1234", nickname="test2")
        # 대여 상품 생성
        self.category = Category.objects.create(name="test")
        self.product = Product.objects.create(
            name="Test Product",
            lender=self.user2,
            product_category=self.category,
            condition="Test Condition",
            purchasing_price=60000,
            rental_fee=5000,
            size="XL",
        )
        self.chatroom = Chatroom.objects.create(
            borrower=self.user,
            lender=self.user2,
            product=self.product,
        )
        # 첫번째 유저 로그인
        self.client.force_login(user=self.user)
        # 두번째 유저 로그인
        self.client.force_login(user=self.user2)

        # url scope를 이용하기 위해 channels의 URLRouter를 직접설정
        self.application = URLRouter(
            [
                path("ws/chat/<int:chatroom_id>/", ChatConsumer.as_asgi()),
            ]
        )

    async def test_단일유저의_웹소켓_접속과_메시지전송_테스트(self) -> None:
        # 웹소켓에 접속 요청
        self.communicator = WebsocketCommunicator(self.application, f"/ws/chat/{self.chatroom.id}/")
        self.communicator.scope["user"] = self.user  # 웹소켓 테스트를 위한 사용자 설정
        self.communicator.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected, subprotocol = await self.communicator.connect()

        # 소켓 연결 확인
        self.assertTrue(connected)

        # 채팅메시지와 유저 정보 전송하기
        data = {
            "message": "Test message",
            "nickname": self.user.nickname,
        }
        await self.communicator.send_json_to(data)

        # 메시지가 올바르게 받아졌는지 확인
        message = await self.communicator.receive_json_from()
        self.assertEqual(message.get("message"), data["message"])
        self.assertEqual(message.get("nickname"), data["nickname"])

        # 보낸 메시지가 데이터베이스에 올바르게 저장되었는지 확인
        count = await database_sync_to_async(self.chatroom.message_set.count)()
        self.assertEqual(count, 1)

        # 데이터 베이스에 저장된 메시지가 유저가 보낸 메시지와 일치하는지 확인
        message = await database_sync_to_async(self.chatroom.message_set.first)()
        self.assertEqual(message.chatroom.id, self.chatroom.id)
        self.assertEqual(message.text, data["message"])
        self.assertEqual(message.sender_id, self.user.id)
        # 메시지의 읽음상태 확인 : 유저 혼자 채팅방에 속한 상황이므로 읽어져선 안됨
        self.assertTrue(message.status)

        # 테스트가 끝났으면 소켓을 정리함
        await self.communicator.disconnect()

    async def test_두유저의_웹소켓_접속과_메시지전송_테스트(self) -> None:
        # 웹소켓에 접속 요청 (첫 번째 유저)
        communicator1 = WebsocketCommunicator(self.application, f"/ws/chat/{self.chatroom.id}/")
        communicator1.scope["user"] = self.user  # 웹소켓 테스트를 위한 사용자 설정
        communicator1.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected1, subprotocol1 = await communicator1.connect()
        self.assertTrue(connected1)  # 소켓 연결 확인

        # 웹소켓에 접속 요청 (두 번째 유저)
        communicator2 = WebsocketCommunicator(self.application, f"/ws/chat/{self.chatroom.id}/")
        communicator2.scope["user"] = self.user2  # 웹소켓 테스트를 위한 사용자 설정
        communicator2.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected2, subprotocol2 = await communicator2.connect()
        self.assertTrue(connected2)  # 소켓 연결 확인

        # 두 유저가 모두 상대가 접속중임을 알 수 있도록 opponent_state가 내려지는지 테스트
        opponent_online_message_to_user1 = await communicator1.receive_json_from()
        self.assertEqual(opponent_online_message_to_user1["opponent_state"], "online")
        opponent_online_message_to_user2 = await communicator2.receive_json_from()
        self.assertEqual(opponent_online_message_to_user2["opponent_state"], "online")
        # 첫번째 유저가 보낼 메시지
        data = {
            "message": "Message from user1",
            "nickname": self.user.nickname,
        }

        # 첫번째 유저가 소켓으로 메시지 보내기
        await communicator1.send_json_to(data)

        # 두번째 유저가 첫번째 유저가 보낸 메시지를 수신하는지 확인
        message_from_user1_to_user2 = await communicator2.receive_json_from()
        self.assertEqual(message_from_user1_to_user2["message"], data["message"])
        self.assertEqual(message_from_user1_to_user2["nickname"], data["nickname"])

        # 메시지를 보낸 첫번째 유저도 같은 메시지를 수신하는지 확인
        message_from_user1_to_user1 = await communicator1.receive_json_from()
        self.assertEqual(message_from_user1_to_user1["message"], data["message"])
        self.assertEqual(message_from_user1_to_user1["nickname"], data["nickname"])

        # 첫번째 유저가 보낸 메시지가 데이터베이스에 올바르게 저장되었는지 확인
        count = await database_sync_to_async(self.chatroom.message_set.count)()
        self.assertEqual(count, 1)

        # 데이터 베이스에 저장된 메시지가 첫번째 유저가 보낸 메시지와 일치하는지 확인
        message = await database_sync_to_async(self.chatroom.message_set.filter(sender=self.user).first)()
        self.assertEqual(message.chatroom.id, self.chatroom.id)
        self.assertEqual(message.text, data["message"])
        self.assertEqual(message.sender_id, self.user.id)

        # 메시지의 읽음상태 확인 : 두번째 유저가 읽었으므로 읽음상태
        self.assertFalse(message.status)

        # 두번째 유저가 보낼 메시지
        data = {
            "message": "Message from user2",
            "nickname": self.user2.nickname,
        }

        # 두번째 유저가 소켓으로 메시지 보내기
        await communicator2.send_json_to(data)

        # 첫번째 유저가 두번째 유저가 보낸 메시지를 수신하는지 확인
        message_from_user2_to_user1 = await communicator1.receive_json_from()
        self.assertEqual(message_from_user2_to_user1["message"], data["message"])
        self.assertEqual(message_from_user2_to_user1["nickname"], data["nickname"])

        # 메시지를 보낸 두번째 유저도 같은 메시지를 수신하는지 확인
        message_from_user2_to_user2 = await communicator2.receive_json_from()
        self.assertEqual(message_from_user2_to_user2["message"], data["message"])
        self.assertEqual(message_from_user2_to_user2["nickname"], data["nickname"])

        # 두번째 유저가 보낸 메시지가 데이터베이스에 올바르게 저장되었는지 확인
        count = await database_sync_to_async(self.chatroom.message_set.count)()
        self.assertEqual(count, 2)

        # 데이터 베이스에 저장된 메시지가 두번째 유저가 보낸 메시지와 일치하는지 확인
        message = await database_sync_to_async(self.chatroom.message_set.filter(sender=self.user2).first)()
        self.assertEqual(message.chatroom.id, self.chatroom.id)
        self.assertEqual(message.text, data["message"])
        self.assertEqual(message.sender_id, self.user2.id)

        # 메시지의 읽음상태 확인 : 두번째 유저가 읽었으므로 읽음상태
        self.assertFalse(message.status)

        # 테스트가 끝났으면 소켓을 정리함
        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_허용되지않은_유저가_채팅방에_접근하는경우(self) -> None:
        invalid_user = await database_sync_to_async(Account.objects.create)(
            email="test3@example.com",
            password="testpw1234",
            nickname="invalid_user",
        )
        communicator = WebsocketCommunicator(self.application, f"/ws/chat/{self.chatroom.id}/")
        communicator.scope["user"] = invalid_user  # 웹소켓 테스트를 위한 사용자 설정
        communicator.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected, code = await communicator.connect()
        self.assertFalse(connected)

    async def test_유효하지_않은_채팅방id로_접속을_시도하는경우(self) -> None:
        # 존재하지 않는 채팅방 ID 사용
        invalid_chatroom_id = 9999

        # 웹소켓에 접속 요청
        communicator = WebsocketCommunicator(self.application, f"/ws/chat/{invalid_chatroom_id}/")
        communicator.scope["user"] = self.user  # 웹소켓 테스트를 위한 사용자 설정
        communicator.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected, subprotocol = await communicator.connect()

        # 연결이 거부되었는지 확인
        self.assertFalse(connected)
