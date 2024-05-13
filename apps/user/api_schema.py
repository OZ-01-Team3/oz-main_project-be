from rest_framework import serializers


class LoginRequestSchema(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class LoginResponseSchema(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class ConfirmRequestSchema(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()


class ConfirmResponseSchema(serializers.Serializer):
    message = serializers.CharField()


class SendRequestSchema(serializers.Serializer):
    email = serializers.EmailField()


class SendResponseSchema(serializers.Serializer):
    message = serializers.CharField()


class SignupRequestSchema(serializers.Serializer):
    email = serializers.EmailField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()
    nickname = serializers.CharField()
    phone = serializers.CharField()


class SignupResponseSchema(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
