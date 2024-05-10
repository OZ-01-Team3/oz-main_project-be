from allauth.account.views import ConfirmEmailView
from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView, LogoutView, UserDetailsView, \
    PasswordChangeView, LoginView
from django.urls import include, path, re_path

from apps.user.views import CustomConfirmEmailView, CustomSignupView, CustomLoginView

# from apps.user.views import CustomConfirmEmailView

# from apps.user.views import ConfirmEmailView

urlpatterns = [
    # path("", include("dj_rest_auth.urls")),
    # path("", include("dj_rest_auth.registration.urls")),
    path('', CustomSignupView.as_view(), name='register'),
    path('password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
    # path('login/', LoginView.as_view(), name='rest_login'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='rest_logout'),
    path('user/', UserDetailsView.as_view(), name='rest_user_details'),
    path('password/change/', PasswordChangeView.as_view(), name='rest_password_change'),
    # re_path(r'^account-confirm-email/(?P<key>[-:\\w]+)/$', ConfirmEmailView.as_view(), name='account_confirm_email'),
    re_path(r"^confirm-email/(?P<key>[-:\w]+)/$", CustomConfirmEmailView.as_view(), name="account_confirm_email"),
    # path("google/", GoogleLogin.as_view(), name="google_login")
]
