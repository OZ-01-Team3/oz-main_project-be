from allauth.account import app_settings
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
        email_address = confirmation.confirm(self.request)
        if not email_address:
        #     return Response(status=status.HTTP_404_NOT_FOUND)
            return render(request, "account/email/confirm-fail.html")
        # return Response(status=status.HTTP_200_OK)
        return render(request, "account/email/confirm-success.html")

    def get_object(self, queryset=None) -> EmailConfirmationHMAC | None:
        key = self.kwargs["key"]
        model = get_emailconfirmation_model()
        email_confirmation = model.from_key(key)
        if not email_confirmation:
            raise Http404()
        return email_confirmation

    def get_queryset(self) -> EmailConfirmation | None:
        return EmailConfirmation.objects.all_valid().select_related("email_address__user")
