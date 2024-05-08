from django.urls import path, include

# from apps.user.views import CustomConfirmEmailView

urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path("", include("dj_rest_auth.registration.urls")),
    # path("confirm-email/", CustomConfirmEmailView.as_view(), name="email_verification_sent")
]
