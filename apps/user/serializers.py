from typing import Any, Dict

from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers

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
