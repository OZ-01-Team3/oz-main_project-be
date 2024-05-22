from typing import Optional

from django.db import models

from apps.common.models import BaseModel
from apps.common.utils import uuid4_generator
from apps.product.models import RentalHistory
from apps.user.models import Account


def upload_to_s3_notification(instance: models.Model, filename: str) -> str:
    # 파일명은 랜덤한 8자리의 문자열과 업로드한 파일이름을 조합해서 만듦(유일성 보장)
    return f"images/notification/{uuid4_generator(length=8)} + {filename}"


class GlobalNotification(BaseModel):
    image = models.ImageField(upload_to=upload_to_s3_notification, blank=True, null=True)
    text = models.TextField()

    def __str__(self) -> str:
        return f"{self.text[:30]}..."


class GlobalNotificationConfirm(BaseModel):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    notification = models.ForeignKey(GlobalNotification, on_delete=models.CASCADE)
    confirm = models.BooleanField(default=False)


class RentalNotification(BaseModel):
    recipient = models.ForeignKey(Account, on_delete=models.CASCADE)
    rental_history = models.ForeignKey(RentalHistory, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    confirm = models.BooleanField(default=False)

    def __str__(self) -> str:
        if self.rental_history:
            if self.rental_history.status == "REQUEST":
                return f"{self.rental_history.product.name}에 대한 {self.rental_history.borrower.nickname}님의 대여 요청 알림"
            elif self.rental_history.status == "ACCEPT":
                return f"{self.rental_history.product.name}에 대한 {self.recipient.nickname}의 대여 요청 수락 알림"
            elif self.rental_history.status == "RETURNED":
                return f"{self.rental_history.product.name} 반납 완료 알림"
            elif self.rental_history.status == "BORROWING":
                return f"{self.rental_history.product.name}에 대한 {self.rental_history.borrower.nickname}님의 대여 진행중 알림"
        return f"{self.text[:30]}..."
