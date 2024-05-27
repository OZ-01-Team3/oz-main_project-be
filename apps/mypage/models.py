from django.db import models

from apps.category.models import Style
from apps.common.models import BaseModel
from apps.user.models import Account


class InterestedStyle(BaseModel):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='users')
    styles = models.ManyToManyField(Style, related_name="styles")
    # styles = models.ForeignKey(Style, on_delete=models.CASCADE, related_name="styles")
