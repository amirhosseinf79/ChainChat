from lib2to3.fixes.fix_input import context

from django.contrib.auth.models import User
from rest_framework import serializers

from main.api.serializers.users import UserSerializer
from main.models import MessageController, Message, Photo, Chat, Video, Group, ChatMember


class GroupSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Group
        fields = ("id", "name", "user", "invite_link")

    def create(self, validated_data):
        return self.Meta.model.filtered_objects.create_group(**validated_data)


class ChatSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(write_only=True, required=True)
    start_with = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Chat
        fields = ("user", "start_with")

    def validate(self, attrs):
        attrs = super().validate(attrs)

        user = attrs.get('user', None)
        start_with = attrs.get('start_with', None)

        if user and start_with and user != start_with:
            user1 = User.objects.filter(id=user)
            user2 = User.objects.filter(id=start_with)

            if not user1.exists() or not user2.exists():
                raise serializers.ValidationError({"details": ["Invalid user provided."]})
        else:
            raise serializers.ValidationError({"details", ["Invalid."]})

        return attrs

    def create(self, validated_data):
        obj = self.Meta.model.objects.create_private_chat(**validated_data)
        return obj

    def get_last_message(self, instance):
        all_messages = instance.get_messages(self.context.get('user', None))
        message_obj = all_messages.first() if all_messages.count() > 0 else None
        data = None

        if message_obj:
            data = {
                "author": UserSerializer(message_obj.author).data,
                "preview": f"{message_obj}",
                "created_at": message_obj.created_at,
            }

        return data

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
            "last_message": self.get_last_message(instance),
        }
        return data


class BaseMessageSerializer(serializers.Serializer):
    author = UserSerializer(read_only=True)
    chat = ChatSerializer(read_only=True, context=context)
    user = serializers.IntegerField(write_only=True, required=True)
    chat_id = serializers.IntegerField(write_only=True, required=True)


class MessageSerializer(BaseMessageSerializer, serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = ("id", "chat", "author", "text", "created_at", "updated_at", "edited_at", "seen_at")
        read_only_fields = ("id", "created_at", "updated_at", "edited_at", "seen_at")


class PhotoSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ("id", "chat", "author", "image", "caption", "created_at", "updated_at", "edited_at", "seen_at")
        read_only_fields = ("id", "created_at", "updated_at", "edited_at", "seen_at")


class VideoSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ("id", "chat", "author", "video", "caption", "created_at", "updated_at", "edited_at", "seen_at")
        read_only_fields = ("id", "created_at", "updated_at", "edited_at", "seen_at")


class AllMessageSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    reply = serializers.SerializerMethodField()
    message = MessageSerializer(read_only=True)
    photo = PhotoSerializer(read_only=True)
    video = VideoSerializer(read_only=True)

    class Meta:
        model = MessageController
        fields = ("message", "photo", "video", "reply", )

    def get_reply(self, instance):
        reply_data = None
        if instance.reply:
            reply_data = {"reply": {"message_id": instance.reply.id, "preview": f"{instance.reply}"}}

        return reply_data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        new_data = {
            "id": 0,
        }
        for k, v in data.items():
            if v and k != "reply":
                new_data.update({f"type": k})
                new_data.update(v)

            elif v and k == "reply":
                new_data.update(v)

        return new_data