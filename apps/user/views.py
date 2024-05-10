from allauth.account import app_settings
from dj_rest_auth.models import get_token_model
from dj_rest_auth.utils import jwt_encode
from dj_rest_auth.views import LoginView
from django.shortcuts import render
from allauth.account.models import (
    EmailConfirmation,
    EmailConfirmationHMAC,
    get_emailconfirmation_model,
)
from allauth.account.views import ConfirmEmailView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.app_settings import api_settings
from dj_rest_auth.registration.views import SocialLoginView, RegisterView
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from allauth.account import app_settings as allauth_account_settings
from allauth.account import app_settings as allauth_settings

from apps.user.models import Account
from config.settings.base import env
from django.utils import timezone

# class GoogleLogin(SocialLoginView):
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = env("GOOGLE_OAUTH2_URL")
#     client_class = OAuth2Client


class CustomSignupView(RegisterView):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        data = self.get_response_data(user)
        res = {
            'access': data["access"],
            'refresh': data["refresh"],
        }
        if res:
            response = Response(
                res,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        else:
            response = Response(status=status.HTTP_204_NO_CONTENT, headers=headers)
        return response


class CustomLoginView(LoginView):
    def get_response(self):
        serializer_class = self.get_response_serializer()

        if api_settings.USE_JWT:
            from rest_framework_simplejwt.settings import (
                api_settings as jwt_settings,
            )
            access_token_expiration = (timezone.now() + jwt_settings.ACCESS_TOKEN_LIFETIME)
            refresh_token_expiration = (timezone.now() + jwt_settings.REFRESH_TOKEN_LIFETIME)
            return_expiration_times = api_settings.JWT_AUTH_RETURN_EXPIRATION
            auth_httponly = api_settings.JWT_AUTH_HTTPONLY

            data = {
                'user': self.user,
                'access': self.access_token,
            }

            if not auth_httponly:
                data['refresh'] = self.refresh_token
            else:
                data['refresh'] = ""

            if return_expiration_times:
                data['access_expiration'] = access_token_expiration
                data['refresh_expiration'] = refresh_token_expiration

            serializer = serializer_class(
                instance=data,
                context=self.get_serializer_context(),
            )
        elif self.token:
            serializer = serializer_class(
                instance=self.token,
                context=self.get_serializer_context(),
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

        data = serializer.data
        data.pop("user", None)
        response = Response(data, status=status.HTTP_200_OK)
        if api_settings.USE_JWT:
            from dj_rest_auth.jwt_auth import set_jwt_cookies
            set_jwt_cookies(response, self.access_token, self.refresh_token)
        return response


class CustomConfirmEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs) -> Response:
        try:
            self.object = self.get_object()
            # if app_settings.CONFIRM_EMAIL_ON_GET:
            return self.post(request, *args, **kwargs)
        except Http404:
            # return Response(status=status.HTTP_404_NOT_FOUND)
            return render(request, "account/email/confirm-fail.html")

    def post(self, request, *args, **kwargs) -> Response:
        self.object = confirmation = self.get_object()
        email_address = confirmation.confirm(self.request)  # EmailAddress 테이블에서 varified True로 변경하고 email 반환, 이미 True인 경우 None 반환
        if not email_address:
        #     return Response(status=status.HTTP_404_NOT_FOUND)
            return render(request, "account/email/confirm-fail.html")
        # return Response(status=status.HTTP_200_OK)
        return render(request, "account/email/confirm-success.html")

    def get_object(self, queryset=None) -> EmailConfirmationHMAC | None:
        """
        get_emailconfirmation_model() -> EmailConfirmation 모델 반환
        from_key() -> url에 있는 인증키로 인증 시도. 잘못된 key이거나 이미 인증된 key일 경우 None 반환
        """
        key = self.kwargs["key"]
        model = get_emailconfirmation_model()
        email_confirmation = model.from_key(key)
        if not email_confirmation:
            raise Http404()
        return email_confirmation

    def get_queryset(self) -> EmailConfirmation | None:
        return EmailConfirmation.objects.all_valid().select_related("email_address__user")
