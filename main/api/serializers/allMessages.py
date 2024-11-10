from lib2to3.fixes.fix_input import context

from rest_framework import serializers

from main.api.serializers.users import UserSerializer
from main.models import MessageController, Message, Photo, Chat, Video, Group, ChatMember


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name", )


class ChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        fields = ()

    def to_representation(self, instance):
        is_group = bool(instance.group)
        user_obj = self.context.get("user", None)

        if is_group:
            title = instance.group.name
        else:

            second_user = ChatMember.objects.filter(chat=instance).exclude(member=user_obj).first()
            if second_user:
                title = (second_user.member.first_name + " " + second_user.member.last_name).strip()
            else:
                title = (user_obj.first_name + " " + user_obj.last_name).strip()

        data = {
            "chat_id": instance.id,
            "is_group": is_group,
            "title": title,
            "created_at": instance.created_at,
            "updated_at": instance.updated_at,
            "is_joined": instance.members.filter(member=user_obj).count() > 0,
            "members": instance.members.all().count(),
        }
        return data


class BaseMessageSerializer(serializers.Serializer):
    author = UserSerializer(read_only=True)
    chat = ChatSerializer(read_only=True, context=context)


class MessageSerializer(BaseMessageSerializer, serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = ("chat", "author", "text", "created_at", "updated_at", "edited_at", "seen_at")


class PhotoSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ("chat", "author", "image", "caption", "created_at", "updated_at", "edited_at", "seen_at")


class VideoSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ("chat", "author", "video", "caption", "created_at", "updated_at", "edited_at", "seen_at")


class AllMessageSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    message = MessageSerializer(read_only=True)
    photo = PhotoSerializer(read_only=True)
    video = VideoSerializer(read_only=True)

    class Meta:
        model = MessageController
        fields = ("message", "photo", "video", )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        new_data = {
            "id": instance.id,
        }
        for k, v in data.items():
            if v:
                new_data.update({f"type": k})
                new_data.update(v)

        return new_data