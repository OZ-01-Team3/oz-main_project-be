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


class GlobalNotificationConfirm(BaseModel):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    notification = models.ForeignKey(GlobalNotification, on_delete=models.CASCADE)
    confirm = models.BooleanField(default=False)


class RentalNotification(BaseModel):
    recipient = models.ForeignKey(Account, on_delete=models.CASCADE)
    rental_history = models.ForeignKey(RentalHistory, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    confirm = models.BooleanField(default=False)
