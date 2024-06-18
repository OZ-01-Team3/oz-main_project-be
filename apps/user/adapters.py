from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from requests import Request
from rest_framework.exceptions import ValidationError

from apps.user.models import Account


class CustomAccountAdapter(DefaultAccountAdapter):  # type: ignore
    def save_user(self, request: Request, user: Any, form: Any, commit: bool = True) -> Any:
        account = super().save_user(request, user, form, False)
        user_field(account, "nickname", request.data.get("nickname"))
        user_field(account, "phone", request.data.get("phone"))
        account.save()
        return account

    def clean_email(self, email: str) -> str:
        if Account.objects.filter(email=email).exists():
            raise ValidationError("This account is already registered.")
        return email
