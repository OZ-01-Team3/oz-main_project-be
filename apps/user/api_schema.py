from rest_framework import serializers

from apps.user.models import Account


class LoginRequestSchema(serializers.Serializer[Account]):
    email = serializers.EmailField()
    password = serializers.CharField()


class LoginResponseSchema(serializers.Serializer[Account]):
    access = serializers.CharField()
    refresh = serializers.CharField()


class ConfirmRequestSchema(serializers.Serializer[Account]):
    email = serializers.EmailField()
    code = serializers.CharField()


class ConfirmResponseSchema(serializers.Serializer[Account]):
    message = serializers.CharField()


class SendRequestSchema(serializers.Serializer[Account]):
    email = serializers.EmailField()


class SendResponseSchema(serializers.Serializer[Account]):
    message = serializers.CharField()


class SignupRequestSchema(serializers.Serializer[Account]):
    email = serializers.EmailField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()
    nickname = serializers.CharField()
    phone = serializers.CharField()


class SignupResponseSchema(serializers.Serializer[Account]):
    access = serializers.CharField()
    refresh = serializers.CharField()


class UserInfoSerializer(serializers.Serializer[Account]):
    nickname = serializers.CharField()
    profile_img = serializers.ImageField()
