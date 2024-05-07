from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.account.models import Account
# from rest_framework_simplwjwt.tokens import AccessToken

from apps.chat.models import Chatroom, Message


class ChatRoomTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = Account.objects.create_user(
            email='test@example.com',
            password='testpw123',
            nickname='testnickname',
            phone='010-1234-5678'
        )
        self.borrower = Account.objects.create_user(
            email='test2@example.com',
            password='testpw1234',
            nickname='testnickname2',
            phone='010-1234-5671'
        )
        # self.token = AccessToken.for_user(self.user)
        self.client.force_login(user=self.user)
    def test_정상적인_채팅방_만들기_요청(self) -> None:
        url = reverse("chatroom")
        data = {
            "borrower": self.borrower.id
        }

        # response = self.client.post(url, data, headers={"Authorization": f"Bearer {self.token}"})
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chatroom.objects.count(), 1)
        self.assertEqual(response.data.get("msg"), "Successful Created Chatroom")

    def test_잘못된_borrower의_아이디로_채팅방을_개설하려는_경우(self) -> None:
        url = reverse("chatroom")
        data = {
            "borrower": 13241
        }

        # response = self.client.post(url, data, headers={"Authorization": f"Bearer {self.token}"})
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Chatroom.objects.count(), 0)


class ChatDetailTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = Account.objects.create_user(
            email='test@example.com',
            password='testpw123',
            nickname='testnickname',
            phone='010-1234-5678'
        )
        self.borrower = Account.objects.create_user(
            email='test2@example.com',
            password='testpw1234',
            nickname='testnickname2',
            phone='010-1234-5671'
        )
        self.chatroom = Chatroom.objects.create(
            borrower=self.borrower,
            lender=self.user
        )
        for i in range(10):
            Message.objects.create(
                chatroom=self.chatroom,
                sender=self.user,
                text=f"test-message-{i}"
            )
            Message.objects.create(
                chatroom=self.chatroom,
                sender=self.borrower,
                text=f"test-message-{i}"
            )
        # self.token = AccessToken.for_user(self.user)
        self.client.force_login(user=self.user)

    def test_채팅에_참여한_유저가_get요청을_보내는_경우(self) -> None:
        url = reverse("chat-detail", kwargs={"chatroom_id": self.chatroom.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Message.objects.count(), len(response.data))

    def test_비정상적인_유저가_get요청을_보내는_경우(self) -> None:
        invaild_user = Account.objects.create_user(
            email='invalid-user@example.com',
            password='testpassword123',
            nickname='invaliduser',
            phone='010-1234-5633'
        )
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
        self.client.force_login(self.borrower)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data.get("msg"), "채팅방에 남은 유저가 없어 채팅방이 삭제되었습니다.")

    def test_비정상적인_유저가_delete요청을_보내는_경우(self) -> None:
        invaild_user = Account.objects.create_user(
            email='invalid-user@example.com',
            password='testpassword123',
            nickname='invaliduser',
            phone='010-1234-5633'
        )
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


