from rest_framework import serializers

from apps.chat.models import Alert, Chatroom, Message


class CreateChatroomSerializer(serializers.ModelSerializer[Chatroom]):
    class Meta:
        model = Chatroom
        fields = "__all__"
        read_only_fields = ["lender"]


class MessageSerializer(serializers.ModelSerializer[Message]):
    sender_nickname = serializers.CharField(source="sender.nickname", read_only=True)

    class Meta:
        model = Message
        exclude = ["sender"]
