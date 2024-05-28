import json
import os

import django
from random import choice

from django.db.models import Q
from locust import between, task
from locust.user.users import HttpUser
from locust_plugins.users.socketio import SocketIOUser


# Django 설정 모듈 지정
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.settings"

# Django 초기화
django.setup()


def get_test_chatroom_info():
    # Q 객체를 사용하여 OR 조건으로 필터링
    from apps.chat.models import Chatroom
    filtered_chatrooms = Chatroom.objects.filter(
        Q(borrower__nickname__icontains="test") | Q(lender__nickname__icontains="test")
    )
    # 필터링된 채팅방의 ID, 대여자, 판매자 목록을 list[dict]로 반환
    return filtered_chatrooms.values("id", "borrower", "lender")


def get_account_model(user_id):
    from apps.user.models import Account
    return Account.objects.get(id=user_id)

# 채팅방 데이터 리스트
chatrooms = get_test_chatroom_info()


class WebSocketUser(SocketIOUser, HttpUser):
    wait_time = between(1, 5)

    def on_start(self) -> None:
        # 랜덤한 채팅방과 유저를 선택
        chatroom_info = choice(chatrooms)
        self.chatroom_id = chatroom_info["id"]
        self.borrower = get_account_model(chatroom_info["borrower"])
        self.lender = get_account_model(chatroom_info["lender"])
        self.sender = choice([self.borrower, self.lender])
        # 선택된 유저로 로그인 요청 보내고 csrf, access 토큰 가져오기
        login_req = self.client.post(
            "http://localhost:8000/api/users/login/",
            data={
                "email": self.sender.email,
                "password": "password123@"
            }
        )
        csrf = login_req.cookies.get("csrftoken")
        session_cookie = login_req.cookies.get("sessionid")
        access = login_req.cookies.get("adfdfd")
        print(f"csrf: {csrf}\n, session: {session_cookie}\n, access: {access}")

        print(f"chatroom_id: {self.chatroom_id}, borrower: {self.borrower.nickname}, lender: {self.lender.nickname}")

        self.connect(
            f"ws://localhost:8000/ws/chat/{self.chatroom_id}/",
            header=[f"X-CSRFToken: {csrf}", f"Authorization: Bearer {access}"],
            cookie="sessionid=" + session_cookie
        )
        print(
            f"Connected to chatroom_id: {self.chatroom_id} as borrower: {self.borrower.nickname}, lender: {self.lender.nickname}"
        )

    @task
    def send_message(self):
        if self.sender == self.borrower:
            message = {
                "text": f"Hello! i want borrow your clothes!",
                "sender": self.sender.nickname,
            }
            self.ws.send(json.dumps(message))
        if self.sender == self.lender:
            message = {
                "text": f"Of course! When are you going to borrow and return it?",
                "sender": self.sender.nickname,
            }
            self.ws.send(json.dumps(message))

    def on_message(self, message):
        response = json.loads(message)
        print(f"Received: {response}")

    if __name__ == "__main__":
        host = "http://127.0.0.1:8000"