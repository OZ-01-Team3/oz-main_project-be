from typing import Any, Dict

from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, UserDetailsSerializer
from django.conf import settings
from django.db.models import Model
from rest_framework import exceptions, serializers

from apps.category.models import Style
from apps.category.serializers import StyleSerializer
from apps.user.models import Account


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
    profile_img = serializers.ImageField(required=False, use_url=True, allow_empty_file=True, allow_null=True)
    # styles = StyleSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Account
        fields = UserDetailsSerializer.Meta.fields + (
            "email",
            "password1",
            "password2",
            "nickname",
            "phone",
            "age",
            "gender",
            "height",
            "region",
            "grade",
            "profile_img",
            # "styles",
        )

    def validate_nickname(self, nickname: str) -> str:
        account_id = self.context["request"].user.id
        if Account.objects.filter(nickname=nickname).exclude(id=account_id).exists():
            raise serializers.ValidationError("This nickname is already in use.")
        return nickname

    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        if "password1" in validated_data and "password2" in validated_data:
            password1 = validated_data.pop("password1")
            password2 = validated_data.pop("password2")
            if password1 and password2 and password1 == password2:
                instance.set_password(password1)
            else:
                raise serializers.ValidationError("Passwords don't match")
        return super().update(instance, validated_data)


class SendCodeSerializer(serializers.Serializer[Dict[str, Any]]):
    email = serializers.EmailField(required=True)

    def validate(self, data: Any) -> Any:
        if Account.objects.filter(email=data.get("email")).exists():
            raise serializers.ValidationError("This email is already registered.")
        return data


class ConfirmEmailSerializer(serializers.Serializer[Dict[str, Any]]):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=7, required=True)

    # def validate_code(self, code: str) -> str:
    #     if len(code) != settings.CODE_LENGTH:
    #         raise serializers.ValidationError("The length of the code is incorrect.")
    #     return code


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
