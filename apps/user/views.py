from allauth.account.models import EmailConfirmationHMAC, EmailConfirmation
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import Account
from config.settings.base import env


# class GoogleLogin(SocialLoginView):
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = env("GOOGLE_OAUTH2_URL")
#     client_class = OAuth2Client


class CustomConfirmEmailView(APIView):
    permission_classes = [AllowAny]

    # def get(self, request, pk, token):
    def get(self, *args, **kwargs):
        self.object = confirmation = self.get_object()
        confirmation.confirm(self.request)
        # return HttpResponseRedirect("/")
        return Response(status=status.HTTP_200_OK)

    def get_object(self, queryset=None):
        key = self.kwargs.get("key")
        email_confirmation = EmailConfirmationHMAC.from_key(key)
        if not email_confirmation:
            if queryset is None:
                queryset = self.get_queryset()
            try:
                email_confirmation = queryset.get(key=key.lower())
            except EmailConfirmation.DoesNotExist:
                return HttpResponseRedirect('/')  # TODO 주소 변경
        return email_confirmation

    def get_queryset(self):
        queryset = EmailConfirmation.objects.all_valid()
        queryset = queryset.select_related("email_address__user")
        return queryset
