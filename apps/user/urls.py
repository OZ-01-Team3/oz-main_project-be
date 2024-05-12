from allauth.account.views import ConfirmEmailView
from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from django.urls import include, path, re_path
from rest_framework_simplejwt.views import TokenVerifyView

from apps.user.views import CustomConfirmEmailView, CustomLoginView, CustomSignupView, SendCodeView, \
    ConfirmEmailView, DeleteUserView

# from apps.user.views import CustomConfirmEmailView

# from apps.user.views import ConfirmEmailView

urlpatterns = [
    # path("", include("dj_rest_auth.urls")),
    # path("", include("dj_rest_auth.registration.urls")),
    path("signup/", CustomSignupView.as_view(), name="register"),
    path("password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="rest_password_reset_confirm"),
    # path('login/', LoginView.as_view(), name='rest_login'),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("user/", UserDetailsView.as_view(), name="rest_user_details"),
    path("leave/", DeleteUserView.as_view(), name="user-detail"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/refresh/", get_refresh_view().as_view(), name="token_refresh"),
    path("password/change/", PasswordChangeView.as_view(), name="rest_password_change"),
    # re_path(r'^account-confirm-email/(?P<key>[-:\\w]+)/$', ConfirmEmailView.as_view(), name='account_confirm_email'),
    # re_path(r"^confirm-email/(?P<key>[-:\w]+)/$", CustomConfirmEmailView.as_view(), name="account_confirm_email"),
    path("send-code", SendCodeView.as_view(), name="send-verification-code"),
    path("verify-email", ConfirmEmailView.as_view(), name="verify-email"),
    # path("google/", GoogleLogin.as_view(), name="google_login")
]
