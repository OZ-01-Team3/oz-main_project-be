from django.db import models

from apps.user.models import Account
from apps.common.utils import uuid4_generator


def upload_to_s3_chat(instance: models.Model, filename: str) -> str:
    # 파일명은 랜덤한 8자리의 문자열과 업로드한 파일이름을 조합해서 만듦(유일성 보장)
    return f"images/chat/{uuid4_generator(length=8)} + {filename}"


class Chatroom(models.Model):
    borrower = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="borrower")
    lender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="lender")
    borrower_status = models.BooleanField(default=True)
    lender_status = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"판매자: {self.borrower}, 대여자: {self.lender}의 채팅방"


class Message(models.Model):
    chatroom = models.ForeignKey(Chatroom, on_delete=models.CASCADE)
    sender = models.ForeignKey(Account, on_delete=models.CASCADE)
    text = models.TextField()
    image = models.ImageField(upload_to=upload_to_s3_chat, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.sender} : {self.text[:30]}.."


class Alert(models.Model):
    chatroom_id = models.ForeignKey(Chatroom, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
