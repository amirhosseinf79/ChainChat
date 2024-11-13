from lib2to3.fixes.fix_input import context

from django.contrib.auth.models import User
from rest_framework import serializers

from main.api.serializers.users import UserSerializer
from main.models import MessageController, Message, Photo, Chat, Video, Group, ChatMember, BlockedUser, SeenUser


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
    is_group = serializers.SerializerMethodField(read_only=True)
    title = serializers.SerializerMethodField(read_only=True)
    is_joined = serializers.SerializerMethodField(read_only=True)
    members = serializers.SerializerMethodField(read_only=True)
    unread_messages = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chat
        fields = ("user", "start_with", "is_group", "is_joined","title",
                  "members", "unread_messages", "last_message")

    def get_is_group(self, instance):
        return bool(instance.group)

    def get_title(self, instance):
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

        return title

    def get_is_joined(self, instance):
        user_obj = self.context.get("user", None)
        return instance.members.filter(member=user_obj).exists()

    def get_members(self, instance):
        return instance.members.filter(is_deleted=False).count()

    def get_unread_messages(self, instance):
        user_obj = self.context.get("user", None)
        return instance.unread_messages_count(user_obj.id)

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

    def validate(self, attrs):
        attrs = super().validate(attrs)

        user = attrs.get('user', None)
        start_with = attrs.get('start_with', None)

        if user and start_with and user != start_with:
            try:
                user1 = User.objects.get(id=user)
                user2 = User.objects.get(id=start_with)
            except User.DoesNotExist:
                raise serializers.ValidationError({"details": ["Invalid user provided."]})

            is_blocked = BlockedUser.filtered_objects.filter(user_id=user2.id, blocked_by_id=user1.id)
            is_blocked_by = BlockedUser.filtered_objects.filter(user_id=user1.id, blocked_by_id=user2.id)

            if is_blocked_by.exists():
                raise serializers.ValidationError({"details": ["Can't create chat with given user."]})
            elif is_blocked.exists():
                data = {"details": ["Can't create chat with given user. unblock user to create chat"]}
                raise serializers.ValidationError(data)
        else:
            raise serializers.ValidationError({"details": ["You can't start chat with yourself."]})

        return attrs

    def create(self, validated_data):
        obj = self.Meta.model.objects.create_private_chat(**validated_data)
        return obj


class BaseMessageSerializer(serializers.Serializer):
    author = UserSerializer(read_only=True)
    chat = ChatSerializer(read_only=True, context=context)
    reply = serializers.SerializerMethodField(read_only=True)
    reply_id = serializers.IntegerField(write_only=True)
    author_id = serializers.IntegerField(write_only=True, required=True)
    chat_id = serializers.IntegerField(write_only=True, required=True)

    def get_reply(self, instance):
        reply_data = None
        if instance.reply:
            reply_data = {"message_id": instance.reply.id, "preview": f"{instance.reply}"}

        return reply_data

    def validate(self, attrs):
        attrs = super().validate(attrs)
        author = attrs.get('author_id', None)
        reply_id = attrs.get('reply_id', None)

        if not author:
            raise serializers.ValidationError({"details": ["Invalid user provided."]})

        if reply_id:
            try:
                MessageController.objects.get(id=reply_id)
            except MessageController.DoesNotExist:
                raise serializers.ValidationError({"details": ["Can't find message with given id to reply."]})

        try:
            check_member = []
            me = User.objects.get(id=author)
            chat_obj = Chat.filtered_objects.get(id=attrs.get('chat_id'))
            if not chat_obj.group:
                chat_members = chat_obj.members.filter(is_deleted=False)
                for member in chat_members:
                    check_member.append(member.member.id)

        except User.DoesNotExist:
            raise serializers.ValidationError({"details": ["Invalid user provided."]})

        except Chat.DoesNotExist:
            raise serializers.ValidationError({"details": ["Invalid chat provided."]})

        is_blocked = []
        for member in check_member:
            is_blocked_obj = BlockedUser.filtered_objects.filter(user_id=member, blocked_by_id=me.id)
            is_blocked_by_obj = BlockedUser.filtered_objects.filter(user_id=me.id, blocked_by_id=member)
            if is_blocked_obj.exists() or is_blocked_by_obj.exists():
                is_blocked.append(member)

        if is_blocked:
            raise serializers.ValidationError({"details": ["Can't send message to given user."]})

        return attrs


class MessageSerializer(BaseMessageSerializer, serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "edited_at")


class PhotoSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "edited_at")


class VideoSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "edited_at")


class SeenUserSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = SeenUser
        fields = ("user", )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        raw_data = {}
        for k, v in data.items():
            raw_data.update(v)
        return raw_data


class AllMessageSerializer(BaseMessageSerializer, serializers.ModelSerializer):
    message = MessageSerializer(read_only=True)
    photo = PhotoSerializer(read_only=True)
    video = VideoSerializer(read_only=True)
    seen_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MessageController
        fields = ("message", "photo", "video", "reply", "seen_by")

    def get_seen_by(self, instance):
        seen_users = instance.seen_users.filter()
        data = SeenUserSerializer(seen_users, many=True).data
        return data


    def to_representation(self, instance):
        data = super().to_representation(instance)
        new_data = {
            "id": 0,
        }
        for k, v in data.items():
            if v and (k == "video" or k == "photo" or k == "message"):
                new_data.update({f"type": k})
                new_data.update(v)

            else:
                new_data.update({k: v})

        return new_data