from typing import Any, Optional
from urllib.request import urlopen

import requests
from dj_rest_auth.app_settings import api_settings
from dj_rest_auth.jwt_auth import set_jwt_cookies
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.utils import jwt_encode
from dj_rest_auth.views import LoginView
from django.conf import settings
from django.contrib.auth import login
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.middleware.csrf import get_token
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.utils import uuid4_generator
from apps.user.api_schema import (
    ConfirmRequestSchema,
    ConfirmResponseSchema,
    LoginRequestSchema,
    LoginResponseSchema,
    SendRequestSchema,
    SendResponseSchema,
    SignupRequestSchema,
    SignupResponseSchema,
)
from apps.user.models import Account
from apps.user.serializers import ConfirmEmailSerializer, SendCodeSerializer
from apps.user.utils import generate_confirmation_code, send_email


@extend_schema(request=SignupRequestSchema, responses=SignupResponseSchema)
class CustomSignupView(RegisterView):  # type: ignore
    permission_classes = [permissions.AllowAny]

    def create(self, request: Request, *args: Any, **kwargs: dict[str, Any]) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        data = self.get_response_data(user)
        res = {
            "access": data["access"],
            "refresh": data["refresh"],
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


@extend_schema(request=LoginRequestSchema, responses=LoginResponseSchema)
class CustomLoginView(LoginView):  # type: ignore
    permission_classes = [permissions.AllowAny]

    def get_response(self) -> Response:
        serializer_class = self.get_response_serializer()

        if api_settings.USE_JWT:
            from rest_framework_simplejwt.settings import api_settings as jwt_settings

            access_token_expiration = timezone.now() + jwt_settings.ACCESS_TOKEN_LIFETIME
            refresh_token_expiration = timezone.now() + jwt_settings.REFRESH_TOKEN_LIFETIME
            return_expiration_times = api_settings.JWT_AUTH_RETURN_EXPIRATION
            auth_httponly = api_settings.JWT_AUTH_HTTPONLY

            data = {
                "user": self.user,
                "access": self.access_token,
            }

            if not auth_httponly:
                data["refresh"] = self.refresh_token
            else:
                data["refresh"] = ""

            if return_expiration_times:
                data["access_expiration"] = access_token_expiration
                data["refresh_expiration"] = refresh_token_expiration

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
            set_jwt_cookies(response, self.access_token, self.refresh_token)
        return response


class DeleteUserView(APIView):
    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=SendRequestSchema, responses=SendResponseSchema)
class SendCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Response) -> Response:
        serializer = SendCodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data.get("email")
        verification_code = generate_confirmation_code()
        send_email(email, verification_code)
        cache.set(email, verification_code, timeout=int(settings.EMAIL_CODE_TIMEOUT))
        return Response({"message": "Verification email sent."}, status=status.HTTP_200_OK)


@extend_schema(request=ConfirmRequestSchema, responses=ConfirmResponseSchema)
class ConfirmEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Response, *args: Any, **kwargs: Any) -> Response:
        serializer = ConfirmEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = request.data.get("email")
        code = request.data.get("code")
        cached_code = cache.get(email)
        if not cached_code:
            return Response(
                {"error": "The confirmation code has expired or does not exist."}, status=status.HTTP_400_BAD_REQUEST
            )
        if code != cached_code:
            return Response({"error": "Invalid confirmation code."}, status=status.HTTP_400_BAD_REQUEST)
        cache.delete(email)
        return Response({"message": "Email confirmation successful."}, status=status.HTTP_200_OK)


class OAuthLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_provider_info(self) -> dict[str, Any]:
        raise NotImplementedError

    @extend_schema(
        request=inline_serializer(name="CodeSeralizer", fields={"code": serializers.CharField()}),
        responses=inline_serializer(
            name="SocialLoginSeralizer",
            fields={
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
                "email": serializers.CharField(),
                "nickname": serializers.CharField(),
                "profile_image": serializers.ImageField(),
            },
        ),
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        code = request.data.get("code")
        if not code:
            return Response({"msg": "인가코드가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        provider_info = self.get_provider_info()
        token_response = self.get_token(code, provider_info)
        if token_response.status_code != status.HTTP_200_OK:
            return Response(
                {"msg": f"{provider_info['name']} 서버로 부터 토큰을 받아오는데 실패하였습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = token_response.json().get("access_token")
        profile_response = self.get_profile(access_token, provider_info)
        if profile_response.status_code != status.HTTP_200_OK:
            return Response(
                {"msg": f"{provider_info['name']} 서버로 부터 프로필 데이터를 받아오는데 실패하였습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.login_process_user(request, profile_response.json(), provider_info)

    def get_token(self, code: str, provider_info: dict[str, Any]) -> requests.Response:
        return requests.post(
            provider_info["token_url"],
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": provider_info["redirect_uri"],
                "client_id": provider_info["client_id"],
                "client_secret": provider_info.get("client_secret"),
            },
        )

    def get_profile(self, access_token: str, provider_info: dict[str, Any]) -> requests.Response:
        return requests.get(
            provider_info["profile_url"],
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
            },
        )

    def login_process_user(
        self, request: Request, profile_res_data: dict[str, Any], provider_info: dict[str, Any]
    ) -> Response:
        # 각 provider의 프로필 데이터 처리 로직
        email = profile_res_data.get(provider_info["email_field"])
        nickname = profile_res_data.get(provider_info["nickname_field"])
        profile_img_url = profile_res_data.get(provider_info["profile_image_field"])
        if provider_info["name"] == "네이버":
            profile_data = profile_res_data.get("response")
            if profile_data:
                email = profile_data.get(provider_info["email_field"])
                nickname = profile_data.get(provider_info["nickname_field"])
                profile_img_url = profile_data.get(provider_info["profile_image_field"])
        elif provider_info["name"] == "카카오":
            account_data = profile_res_data.get("kakao_account")
            if account_data:
                email = account_data.get(provider_info["email_field"])
                profile_data = account_data.get("profile")
                if profile_data:
                    nickname = profile_data.get(provider_info["nickname_field"])
                    profile_img_url = profile_data.get(provider_info["profile_image_field"])

        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            user = self.create_user(email=email, nickname=nickname, profile_img_url=profile_img_url, provider_info=provider_info)  # type: ignore

        # 로그인해서 세션획득
        login(request, user)

        access_token, refresh_token = jwt_encode(user)
        response_data = {
            "access": str(access_token),
            "refresh": str(refresh_token),
            "email": user.email,
            "nickname": user.nickname,
        }
        if user.profile_img:
            response_data["profile_image"] = user.profile_img.url
        # set_cookie csrftoken
        response = Response(response_data, status=status.HTTP_200_OK)
        response.set_cookie(
            key="csrftoken",
            value=get_token(request),
            domain=settings.CSRF_COOKIE_DOMAIN,
            samesite=None,
            secure=settings.CSRF_COOKIE_SECURE,
            httponly=settings.CSRF_COOKIE_HTTPONLY
        )
        return response

    def create_user(
        self, email: str, nickname: str, profile_img_url: Optional[str], provider_info: dict[str, Any]
    ) -> Account:
        if profile_img_url:
            image_response = urlopen(profile_img_url)
            image_content = image_response.read()
            profile_image = ContentFile(image_content, name=f"{provider_info['name']}-profile-{uuid4_generator(8)}.jpg")
            user = Account.objects.create(email=email, nickname=nickname, profile_img=profile_image)
        else:
            user = Account.objects.create(email=email, nickname=nickname)
        user.save()
        return user


class KakaoLoginView(OAuthLoginView):
    def get_provider_info(self) -> dict[str, Any]:
        return {
            "name": "카카오",
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "token_url": "https://kauth.kakao.com/oauth/token",
            "profile_url": "https://kapi.kakao.com/v2/user/me",
            "client_id": settings.KAKAO_CLIENT_ID,
            "client_secret": settings.KAKAO_CLIENT_SECRET,
            "email_field": "email",
            "nickname_field": "nickname",
            "profile_image_field": "profile_image_url",
        }


class GoogleLoginView(OAuthLoginView):
    def get_provider_info(self) -> dict[str, Any]:
        return {
            "name": "구글",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "token_url": "https://oauth2.googleapis.com/token",
            "profile_url": "https://www.googleapis.com/oauth2/v1/userinfo",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_SECRET,
            "email_field": "email",
            "nickname_field": "name",
            "profile_image_field": "picture",
        }


class NaverLoginView(OAuthLoginView):
    def get_provider_info(self) -> dict[str, Any]:
        return {
            "name": "네이버",
            "redirect_uri": settings.NAVER_REDIRECT_URI,
            "token_url": "https://nid.naver.com/oauth2.0/token",
            "profile_url": "https://openapi.naver.com/v1/nid/me",
            "client_id": settings.NAVER_CLIENT_ID,
            "client_secret": settings.NAVER_CLIENT_SECRET,
            "email_field": "email",
            "nickname_field": "nickname",
            "profile_image_field": "profile_image",
        }


# class CustomConfirmEmailView(APIView):
#     permission_classes = [AllowAny]
#
#     def get(self, request: Request, *args: Any, **kwargs: dict[str, Any]) -> HttpResponse:
#         try:
#             self.object = self.get_object()
#             # if app_settings.CONFIRM_EMAIL_ON_GET:
#             return self.post(request, *args, **kwargs)
#         except Http404:
#             # return Response(status=status.HTTP_404_NOT_FOUND)
#             return render(request, "account/email/confirm-fail.html")
#
#     def post(self, request: Request, *args: Any, **kwargs: dict[str, Any]) -> HttpResponse:
#         self.object = confirmation = self.get_object()
#         email_address = confirmation.confirm(  # type: ignore
#             request
#         )  # EmailAddress 테이블에서 varified True로 변경하고 email 반환, 이미 True인 경우 None 반환
#         if not email_address:
#             #     return Response(status=status.HTTP_404_NOT_FOUND)
#             return render(request, "account/email/confirm-fail.html")
#         # return Response(status=status.HTTP_200_OK)
#         return render(request, "account/email/confirm-success.html")
#
#     def get_object(self, queryset: Any = None) -> EmailConfirmationHMAC | None:
#         """
#         get_emailconfirmation_model() -> EmailConfirmation 모델 반환
#         from_key() -> url에 있는 인증키로 인증 시도. 잘못된 key이거나 이미 인증된 key일 경우 None 반환
#         """
#         key = self.kwargs["key"]
#         model = get_emailconfirmation_model()
#         email_confirmation = model.from_key(key)
#         if not email_confirmation:
#             raise Http404()
#         return email_confirmation
#
#     def get_queryset(self) -> EmailConfirmation | None:
#         return EmailConfirmation.objects.all_valid().select_related("email_address__user")
