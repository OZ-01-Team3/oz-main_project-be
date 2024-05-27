import base64
import json
from datetime import datetime, timedelta

from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase
from django.urls import path
from django_redis import get_redis_connection

from apps.category.models import Category
from apps.chat.consumers import ChatConsumer
from apps.chat.models import Chatroom
from apps.chat.utils import get_group_name
from apps.notification.consumers import NotificationConsumer
from apps.notification.models import (
    GlobalNotification,
    GlobalNotificationConfirm,
    RentalNotification,
)
from apps.product.models import Product, ProductImage, RentalHistory
from apps.user.models import Account


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return "data:image/jpeg;base64," + encoded_string


class BaseTestCase(TransactionTestCase):
    def setUp(self) -> None:
        # 요청을 보낼 유저 생성
        self.borrower = Account.objects.create_user(
            email="test@example.com", password="testpw123", nickname="borrower1"
        )
        # 대여 상품 판매자 생성
        self.lender = Account.objects.create_user(email="test2@example.com", password="testpw1234", nickname="lender1")
        # 대여 상품 생성
        self.category = Category.objects.create(name="test")
        self.product = Product.objects.create(
            name="Test Product",
            lender=self.lender,
            product_category=self.category,
            condition="Test Condition",
            purchase_date=datetime.now(),
            purchase_price=60000,
            rental_fee=5000,
            size="XL",
        )
        # 상품 이미지 생성
        self.image = SimpleUploadedFile(
            name="test.jpg", content=open("static/test/test.jpeg", "rb").read(), content_type="image/jpeg"
        )
        self.encoded_image = encode_image_to_base64("static/test/test.jpeg")
        self.product_image = ProductImage.objects.create(product=self.product, image=self.image)
        # 채팅방 생성
        self.chatroom = Chatroom.objects.create(product=self.product, borrower=self.borrower, lender=self.lender)
        # 첫번째 유저 로그인
        self.client.force_login(user=self.borrower)
        # 두번째 유저 로그인
        self.client.force_login(user=self.lender)

        # url scope를 이용하기 위해 channels의 URLRouter를 직접설정
        self.application = URLRouter(
            [
                path("ws/notification/", NotificationConsumer.as_asgi()),
                path("ws/chat/<int:chatroom_id>", ChatConsumer.as_asgi()),
            ]
        )
        self.redis_conn = get_redis_connection("default")


class RentalNotificationTestCase(BaseTestCase):
    async def test_RentalHistory가_처음_생성될때_알림메시지_테스트(self) -> None:
        # 웹소켓에 접속 요청 (첫 번째 유저)
        communicator1 = WebsocketCommunicator(self.application, f"/ws/notification/")
        communicator1.scope["user"] = self.borrower  # 웹소켓 테스트를 위한 사용자 설정
        communicator1.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected1, subprotocol1 = await communicator1.connect()
        self.assertTrue(connected1)  # 소켓 연결 확인

        # 웹소켓에 접속 요청 (두 번째 유저)
        communicator2 = WebsocketCommunicator(self.application, f"/ws/notification/")
        communicator2.scope["user"] = self.lender  # 웹소켓 테스트를 위한 사용자 설정
        communicator2.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected2, subprotocol2 = await communicator2.connect()
        self.assertTrue(connected2)  # 소켓 연결 확인

        # 상품 대여 요청 생성
        rental_history = await database_sync_to_async(RentalHistory.objects.create)(
            product=self.product,
            borrower=self.borrower,
            rental_date=datetime.now(),
            return_date=datetime.now() + timedelta(days=3),
            status="REQUEST",
        )

        # 정상적으로 생성되었는지 확인
        self.assertEqual(await database_sync_to_async(RentalHistory.objects.count)(), 1)

        # 판매자에게 요청알림이 갔는지 확인
        req_notification = await communicator2.receive_json_from()

        self.assertEqual(req_notification["product_name"], rental_history.product.name)
        self.assertEqual(req_notification["image"], self.product_image.image.url)
        self.assertEqual(req_notification["borrower"], rental_history.borrower.nickname)
        self.assertEqual(req_notification["lender"], rental_history.product.lender.nickname)
        self.assertEqual(req_notification["type"], "rental_notification")
        self.assertEqual(req_notification["status"], rental_history.status)
        self.assertEqual(req_notification["return_date"], rental_history.return_date.isoformat())
        self.assertEqual(req_notification["rental_date"], rental_history.rental_date.isoformat())

        # 대여 알림이 생성되었는지 테스트
        self.assertTrue(
            await database_sync_to_async(
                RentalNotification.objects.filter(
                    recipient=self.lender, rental_history=rental_history, confirm=False
                ).exists
            )()
        )

        rental_notification = await database_sync_to_async(RentalNotification.objects.get)(
            recipient=self.lender, rental_history=rental_history, confirm=False
        )

        # 알림읽기테스트
        await communicator2.send_json_to(
            {"command": "rental_notification_confirm", "notification_id": rental_notification.id}
        )
        updated_confirm = await database_sync_to_async(RentalNotification.objects.get)(
            rental_history=rental_history, recipient=self.lender
        )
        self.assertFalse(updated_confirm.confirm)

        # 소켓 연결 해제
        await communicator1.disconnect()
        await communicator2.disconnect()


class ChatNotificationTestCase(BaseTestCase):
    async def test_새로운_채팅_메시지가_생성될때_알림메시지_테스트(self) -> None:
        # 알림 웹소켓에 접속 요청 (상품 판매 유저 == 메시지를 받는 유저)
        notification_communicator = WebsocketCommunicator(self.application, f"/ws/notification/")
        notification_communicator.scope["user"] = self.lender  # 웹소켓 테스트를 위한 사용자 설정
        notification_communicator.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected1, subprotocol1 = await notification_communicator.connect()
        self.assertTrue(connected1)  # 소켓 연결 확인

        # 빌리는 유저(메시지를 보낼유저)가 채팅 웹소켓에 접속
        chat_communicator = WebsocketCommunicator(self.application, f"/ws/chat/{self.chatroom.id}")
        chat_communicator.scope["user"] = self.borrower
        chat_communicator.scope["type"] = "websocket"
        connected2, subprotocol2 = await chat_communicator.connect()
        # 채팅 소켓 연결 확인
        self.assertTrue(connected2)

        # 상대방 오프라인 여부 확인
        alert = await chat_communicator.receive_json_from()
        self.assertTrue(alert.get("opponent_state"), "offline")

        # 새로운 채팅 메시지 생성
        # 채팅메시지와 유저 정보 전송하기
        data = {"text": "Test message", "image": self.encoded_image, "sender": self.borrower.nickname}
        await chat_communicator.send_json_to(data)

        # 메시지가 올바르게 받아졌는지 확인
        message = await chat_communicator.receive_json_from()
        self.assertEqual(message.get("text"), data["text"])
        self.assertTrue(message.get("image"))
        self.assertEqual(message.get("nickname"), data["sender"])
        self.assertEqual(message.get("type"), "chat_message")

        # 보낸 메시지가 데이터베이스에 저장되지않고 레디스에 올바르게 저장되었는지 확인
        count = await database_sync_to_async(self.chatroom.message_set.count)()
        self.assertEqual(count, 0)
        key = f"{get_group_name(chatroom_id=self.chatroom.id)}_messages"

        stored_message = self.redis_conn.lrange(key, -1, -1)
        redis_message = json.loads(stored_message[0])

        self.assertEqual(redis_message.get("chatroom_id"), self.chatroom.id)
        self.assertEqual(redis_message.get("text"), data["text"])
        self.assertEqual(redis_message.get("sender_id"), self.borrower.id)
        self.assertEqual(redis_message.get("image"), message.get("image"))

        # 메시지의 읽음상태 확인 : 유저 혼자 채팅방에 속한 상황이므로 읽어져선 안됨
        self.assertTrue(redis_message.get("status"))

        # 판매자에게 안읽은 메시지 알림이 전송되었는지 확인
        chat_notification = await notification_communicator.receive_json_from(timeout=1)
        self.assertEqual(chat_notification["text"], data["text"])

        await notification_communicator.disconnect()
        await chat_communicator.disconnect()


class GlobalNotificationTestCase(TransactionTestCase):
    def setUp(self) -> None:
        # 알림을 받을 유저 생성
        self.user1 = Account.objects.create_user(email="test@example.com", password="testpw123", nickname="testuser1")
        self.user2 = Account.objects.create_user(email="test2@example.com", password="testpw1234", nickname="testuser2")
        # 알림 이미지 생성
        self.image = SimpleUploadedFile(
            name="test_image.jpg", content=open("static/test/test.jpeg", "rb").read(), content_type="image/jpeg"
        )
        # 첫번째 유저 로그인
        self.client.force_login(user=self.user1)
        # 두번째 유저 로그인
        self.client.force_login(user=self.user2)

        # url scope를 이용하기 위해 channels의 URLRouter를 직접설정
        self.application = URLRouter(
            [
                path("ws/notification/", NotificationConsumer.as_asgi()),
            ]
        )

    async def test_모든_사용자에게_공통으로_적용되는_알림_테스트(self) -> None:
        # 웹소켓에 접속 요청 (첫 번째 유저)
        communicator1 = WebsocketCommunicator(self.application, f"/ws/notification/")
        communicator1.scope["user"] = self.user1  # 웹소켓 테스트를 위한 사용자 설정
        communicator1.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected1, subprotocol1 = await communicator1.connect()
        self.assertTrue(connected1)  # 소켓 연결 확인

        # 웹소켓에 접속 요청 (두 번째 유저)
        communicator2 = WebsocketCommunicator(self.application, f"/ws/notification/")
        communicator2.scope["user"] = self.user2  # 웹소켓 테스트를 위한 사용자 설정
        communicator2.scope["type"] = "websocket"  # 웹소켓 통신임을 설정
        connected2, subprotocol2 = await communicator2.connect()
        self.assertTrue(connected2)  # 소켓 연결 확인

        # 전역으로 전송할 알림 생성
        notification = await database_sync_to_async(GlobalNotification.objects.create)(
            image=self.image, text=f"{self.user1.nickname}을 위한 알림메시지"
        )
        self.assertEqual(await database_sync_to_async(GlobalNotification.objects.count)(), 1)

        # 알림이 전송되었는지 테스트
        notification_for_user1 = await communicator1.receive_json_from()
        notification_for_user2 = await communicator2.receive_json_from()

        self.assertEqual(notification_for_user1["image"], notification.image.url)
        self.assertEqual(notification_for_user1["text"], notification.text)
        self.assertEqual(notification_for_user2["image"], notification.image.url)
        self.assertEqual(notification_for_user2["text"], notification.text)

        # 알림 확인 모델이 생성되었는지 테스트
        self.assertTrue(
            await database_sync_to_async(
                GlobalNotificationConfirm.objects.filter(
                    notification=notification, user=self.user1, confirm=False
                ).exists
            )()
        )
        self.assertTrue(
            await database_sync_to_async(
                GlobalNotificationConfirm.objects.filter(
                    notification=notification, user=self.user2, confirm=False
                ).exists
            )()
        )

        # 유저1의 알림 읽기 테스트
        await communicator1.send_json_to({"command": "global_notification_confirm", "notification_id": notification.id})
        user1_confirm_instance = await database_sync_to_async(GlobalNotificationConfirm.objects.get)(
            notification=notification, user=self.user1
        )
        self.assertFalse(user1_confirm_instance.confirm)

        # 유저2의 알림 읽기 테스트
        await communicator1.send_json_to({"command": "global_notification_confirm", "notification_id": notification.id})
        user2_confirm_instance = await database_sync_to_async(GlobalNotificationConfirm.objects.get)(
            notification=notification, user=self.user2
        )
        self.assertFalse(user2_confirm_instance.confirm)

        # 소켓 정리
        await communicator1.disconnect()
        await communicator2.disconnect()
