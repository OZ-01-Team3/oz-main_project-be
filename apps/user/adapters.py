from typing import Any

from allauth import app_settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from allauth.utils import import_attribute
from django.conf import settings
from requests import Request
from rest_framework.exceptions import ValidationError

from apps.user.models import Account
from config.settings.settings import FRONT_CONFIRM_URL


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

    # def get_email_confirmation_url(self, request: Request, emailconfirmation: Any) -> Any:
    #     """
    #     이메일 확인 링크 커스텀
    #     """
    #     url = settings.FRONT_CONFIRM_URL + emailconfirmation.key
    #     return url


# def get_adapter(request=None):
#     return import_attribute(app_settings.ADAPTER)(request)
