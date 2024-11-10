from rest_framework import serializers

from main.api.serializers.allMessages import ChatSerializer
from main.api.serializers.users import UserSerializer
from main.models import ChatMember


class ChatMemberSerializer(serializers.ModelSerializer):
    chat = ChatSerializer(read_only=True)
    member = UserSerializer(read_only=True)

    class Meta:
        model = ChatMember
        fields = ("chat", "member")

    def to_representation(self, instance):
        data = {
            "id": instance.member.id,
            "username": instance.member.username,
            "email": instance.member.email,
            "first_name": instance.member.first_name,
            "last_name": instance.member.last_name,
        }
        return data
