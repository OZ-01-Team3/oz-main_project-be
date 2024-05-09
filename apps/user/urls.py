from allauth.account.views import ConfirmEmailView
from dj_rest_auth.registration.views import VerifyEmailView
from django.urls import include, path, re_path

from apps.user.views import CustomConfirmEmailView

# from apps.user.views import CustomConfirmEmailView

# from apps.user.views import ConfirmEmailView

urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path("", include("dj_rest_auth.registration.urls")),
    # re_path(r'^account-confirm-email/(?P<key>[-:\\w]+)/$', ConfirmEmailView.as_view(), name='account_confirm_email'),
    re_path(r"^confirm-email/(?P<key>[-:\w]+)/$", CustomConfirmEmailView.as_view(), name="account_confirm_email"),
    # path("google/", GoogleLogin.as_view(), name="google_login")
]
