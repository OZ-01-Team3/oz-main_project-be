from allauth.account.views import ConfirmEmailView
from dj_rest_auth.registration.views import VerifyEmailView
from django.urls import path, include, re_path

# from apps.user.views import ConfirmEmailView

urlpatterns = [
    # path("", include("allauth.urls")),
    path("", include("dj_rest_auth.urls")),
    path("", include("dj_rest_auth.registration.urls")),
    # path("account-confirm-email/", CustomConfirmEmailView.as_view(), name="confirm-email")
    re_path(r'^account-confirm-email/$', VerifyEmailView.as_view(), name='account_email_verification_sent'),
    # 유저가 클릭한 이메일(=링크) 확인
    re_path(r'^account-confirm-email/(?P<key>[-:\\w]+)/$', ConfirmEmailView.as_view(), name='account_confirm_email'),

]
