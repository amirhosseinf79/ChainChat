from rest_framework import serializers

from main.api.serializers.allMessages import ChatSerializer
from main.api.serializers.users import UserSerializer
from main.models import ChatMember


class ChatMemberSerializer(serializers.ModelSerializer):
    # chat = ChatSerializer(read_only=True)
    # member = UserSerializer(read_only=True)
    id = serializers.SerializerMethodField(read_only=True)
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.member.id

    def get_username(self, obj):
        return obj.member.username

    def get_email(self, obj):
        return obj.member.email

    def get_first_name(self, obj):
        return obj.member.first_name

    def get_last_name(self, obj):
        return obj.member.last_name

    class Meta:
        model = ChatMember
        fields = ("id", "username", "email", "first_name", "last_name")
