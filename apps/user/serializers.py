from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers

from apps.user.models import Account


class SignupSerializer(RegisterSerializer):
    nickname = serializers.CharField()
    phone = serializers.CharField()

    class Meta:
        model = Account
        fields = ("email", "password1", "password2", "nickname", "phone")

    def validate_nickname(self, nickname):
        if Account.objects.filter(nickname=nickname).exists():
            raise serializers.ValidationError("This nickname is already in use.")
        return nickname


class UserInfoSerializer(UserDetailsSerializer):
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

    def validate_nickname(self, nickname):
        account_id = self.context["request"].user.id
        if Account.objects.filter(nickname=nickname).exclude(id=account_id).exists():
            raise serializers.ValidationError("This nickname is already in use.")
        return nickname
