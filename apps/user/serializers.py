from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, UserDetailsSerializer
from rest_framework import exceptions, serializers

from apps.user.models import Account
from config.settings import settings


class SignupSerializer(RegisterSerializer):  # type: ignore
    nickname = serializers.CharField()
    phone = serializers.CharField()

    class Meta:
        model = Account
        fields = ("email", "password1", "password2", "nickname", "phone")

    def validate_nickname(self, nickname: str) -> str:
        if Account.objects.filter(nickname=nickname).exists():
            raise serializers.ValidationError("This nickname is already in use.")
        return nickname


class UserInfoSerializer(UserDetailsSerializer):  # type: ignore
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    nickname = serializers.CharField()
    phone = serializers.CharField()
    age = serializers.IntegerField(required=False)
    gender = serializers.CharField(required=False, allow_blank=True)
    height = serializers.IntegerField(required=False)
    region = serializers.CharField(required=False, allow_blank=True)
    grade = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Account
        fields = ("email", "password1", "password2", "nickname", "phone", "age", "gender", "height", "region", "grade")

    def validate_nickname(self, nickname: str) -> str:
        account_id = self.context["request"].user.id
        if Account.objects.filter(nickname=nickname).exclude(id=account_id).exists():
            raise serializers.ValidationError("This nickname is already in use.")
        return nickname


# class CustomLoginSerializer(LoginSerializer):
#     email = serializers.EmailField(required=False, allow_blank=True)
#     password = serializers.CharField(style={'input_type': 'password'})
#
#     def validate(self, attrs):
#         username = attrs.get('username')
#         email = attrs.get('email')
#         password = attrs.get('password')
#         user = self.get_auth_user(username, email, password)
#
#         if not user:
#             msg = _('Unable to log in with provided credentials.')
#             raise exceptions.ValidationError(msg)
#
#         # Did we get back an active user?
#         self.validate_auth_user_status(user)
#
#         # If required, is the email verified?
#         if 'dj_rest_auth.registration' in settings.INSTALLED_APPS:
#             self.validate_email_verification_status(user, email=email)
#
#         # attrs['user'] = user
#         attrs.pop("user", None)
#         return attrs
