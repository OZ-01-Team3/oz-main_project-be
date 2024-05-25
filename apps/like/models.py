from django.db import models

from apps.common.models import BaseModel
from apps.product.models import Product
from apps.user.models import Account


# Create your models here.
class Like(BaseModel):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_user_product"),
        ]
