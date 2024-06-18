from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.views import (
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from apps.user.views import (
    ConfirmEmailView,
    CustomLoginView,
    CustomSignupView,
    DeleteUserView,
    GoogleLoginView,
    KakaoLoginView,
    NaverLoginView,
    SendCodeView,
)

urlpatterns = [
    path("signup/", CustomSignupView.as_view(), name="signup"),
    path("password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="rest_password_reset_confirm"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("login/social/kakao/", KakaoLoginView.as_view(), name="kakao_login"),
    path("login/social/google/", GoogleLoginView.as_view(), name="google_login"),
    path("login/social/naver/", NaverLoginView.as_view(), name="naver_login"),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("detail/", UserDetailsView.as_view(), name="rest_user_details"),
    path("leave/", DeleteUserView.as_view(), name="delete-user"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/refresh/", get_refresh_view().as_view(), name="token_refresh"),
    path("password/change/", PasswordChangeView.as_view(), name="rest_password_change"),
    path("send-code/", SendCodeView.as_view(), name="send-code"),
    path("confirm-email/", ConfirmEmailView.as_view(), name="confirm-email"),
]
