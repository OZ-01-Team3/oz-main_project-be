from typing import Any
from urllib.request import urlopen

import requests
from dj_rest_auth.app_settings import api_settings
from dj_rest_auth.jwt_auth import set_jwt_cookies
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.utils import jwt_encode
from dj_rest_auth.views import LoginView
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
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


class KakaoLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        code = request.data.get("code")  # 프론트에서 보내준 코드
        # 카카오 oauth 토큰 발급 url로 code가 담긴 post 요청을 보내 응답을 받는다.
        CLIENT_ID = settings.KAKAO_CLIENT_ID
        REDIRECT_URI = settings.REDIRECT_URI
        token_response = requests.post(
            "https://kauth.kakao.com/oauth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
            },
        )

        if token_response.status_code != status.HTTP_200_OK:
            return Response(
                {"msg": "카카오 서버로 부터 토큰을 받아오는데 실패하였습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # 응답으로부터 액세스 토큰을 가져온다.
        access_token = token_response.json().get("access_token")
        response = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
            },
        )

        if response.status_code != status.HTTP_200_OK:
            return Response(
                {"msg": "카카오 서버로 부터 프로필 데이터를 받아오는데 실패하였습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        response_data = response.json()
        kakao_account = response_data["kakao_account"]
        profile = kakao_account.get("profile")
        requests.post("https://kapi.kakao.com/v1/user/logout", headers={"Authorization": f"Bearer {access_token}"})
        try:
            user = Account.objects.get(email=kakao_account.get("email"))
            access_token, refresh_token = jwt_encode(user)
            response = Response(
                {
                    "access": str(access_token),
                    "refresh": str(refresh_token),  # type: ignore
                    "email": user.email,
                    "nickname": user.nickname,
                    "profile_image": user.profile_img.url,
                },
                status=status.HTTP_200_OK,
            )
            # set_jwt_cookies(response, access_token, refresh_token)
            return response  # type: ignore

        except Account.DoesNotExist:
            # 이미지를 다운로드하여 파일 객체로 가져옴
            image_response = urlopen(profile.get("profile_image_url"))
            image_content = image_response.read()
            kakao_profile_image = ContentFile(image_content, name=f"kakao-profile-{uuid4_generator(8)}.jpg")
            user = Account.objects.create(
                email=kakao_account.get("email"),
                nickname=profile.get("nickname"),
                profile_img=kakao_profile_image,
            )
            user.set_unusable_password()
            access_token, refresh_token = jwt_encode(user)
            response = Response(
                {
                    "access": str(access_token),
                    "refresh": str(refresh_token),  # type: ignore
                    "email": user.email,
                    "nickname": user.nickname,
                    "profile_image": user.profile_img.url,
                },
                status=status.HTTP_200_OK,
            )
            # set_jwt_cookies(response, access_token, refresh_token)
            return response  # type: ignore
        except Exception as e:
            return Response({"msg": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        code = request.data.get("code")

        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_SECRET
        redirect_uri = settings.REDIRECT_URI

        if not code:
            return Response({"msg": "인가코드가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 인가코드를 통해 토큰을 가져오는 요청
        token_req = requests.post(
            # f"https://oauth2.googleapis.com/token?client_id={client_id}&client_secret={client_secret}&code={code}&grant_type=authorization_code&redirect_uri={redirect_uri}"
            "https://oauth2.googleapis.com/token",
            headers={
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
            },
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        # 요청의 응답을 json 파싱
        token_req_json = token_req.json()
        if token_req_json.status_code != 200:
            return Response({"msg": token_req_json.get("error")}, status=status.HTTP_400_BAD_REQUEST)
        # 파싱된 데이터중 액세스 토큰을 가져옴
        google_access_token = token_req_json.get("access_token")

        # 가져온 액세스토큰을 통해 사용자 정보에 접근하는 요청
        info_response = requests.get(
            f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={google_access_token}"
        )

        # 상태코드로 요청이 실패했는지 확인
        if info_response.status_code != 200:
            return Response(
                {"message": "구글 api로부터 액세스토큰을 받아오는데 실패했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 요청의 응답을 json 파싱
        res_json = info_response.json()
        # 파싱된 데이터중 이메일값을 가져옴
        email = res_json.get("email")
        # 파싱된 데이터중 닉네임을 가져옴
        nickname = res_json.get("nickname")
        try:
            user = Account.objects.get(email=email)
            access_token, refresh_token = jwt_encode(user)
            response_data = {
                "access": str(access_token),
                "refresh": str(refresh_token),
                "email": user.email,
                "nickname": user.nickname,
            }
            if user.profile_img:
                response_data["profile_image"] = user.profile_img.url
            response = Response(response_data, status=status.HTTP_200_OK)
            # if api_settings.USE_JWT:
            #     set_jwt_cookies(response, access_token, refresh_token)
            return response
        except Account.DoesNotExist:
            # 파싱된 데이터에서 프로필 이미지 url을 가져와서 파일로 변환
            image_response = urlopen(res_json.get("picture"))
            image_content = image_response.read()
            google_profile_image = ContentFile(image_content, name=f"google-profile-{uuid4_generator(8)}.jpg")
            # 가져온 이메일, 닉네임, 프로필 이미지를 통해 유저 생성
            user = Account.objects.create(email=email, nickname=nickname, profile_img=google_profile_image)
            user.set_unusable_password()
            access_token, refresh_token = jwt_encode(user)
            response_data = {
                "access": str(access_token),
                "refresh": str(refresh_token),
                "email": user.email,
                "nickname": user.nickname,
            }
            if user.profile_img:
                response_data["profile_image"] = user.profile_img.url
            response = Response(response_data, status=status.HTTP_200_OK)
            # if api_settings.USE_JWT:
            #     set_jwt_cookies(response, access_token, refresh_token)
            return response

        except Exception as e:
            # 가입이 필요한 회원
            return Response({"msg": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
