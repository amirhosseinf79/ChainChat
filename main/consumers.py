import json
from datetime import datetime

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from main.api.serializers.allMessages import ChatSerializer
from main.models import Chat, ChatMember


def convert_datetime_to_strings(data):
    if isinstance(data, list):
        return [convert_datetime_to_strings(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_datetime_to_strings(value) for key, value in data.items()}
    elif isinstance(data, datetime):
        return data.isoformat()
    return data

@database_sync_to_async
def serialize_chat(chat_obj, user_obj):
    data = ChatSerializer(chat_obj, context={"user": user_obj}).data
    return convert_datetime_to_strings(data)

@database_sync_to_async
def get_chat(chat_id):
    try:
        obj = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        obj = None

    return obj

@database_sync_to_async
def change_online_status(user_obj, is_online):
    user_obj.profile.is_online = is_online
    return user_obj.profile.save()

async def notify_user_friends(self, user_obj):
    chats = Chat.filtered_objects.filter(group__isnull=True, members__member=user_obj).distinct()
    main_data = {}
    async for chat in chats:
        raw_data = {
            "type": "message.send",
            "updated_chat": await serialize_chat(chat, user_obj),
            "user_status": await get_user_profile(user_obj),
            "message": None,
            "action": "online_status",
        }
        users = await get_chat_members(chat)

        for uid in users:
            main_data[uid] = raw_data.copy()

    for uid, data in main_data.items():
        if uid == f"user_{user_obj.id}":
            continue
        await self.channel_layer.group_send(uid, data)

async def get_chat_members(chat_obj):
    tmp = ChatMember.filtered_objects.filter(chat=chat_obj).distinct().values_list("member_id", flat=True).distinct()
    return [f"user_{uid}" async for uid in tmp]

@database_sync_to_async
def get_user_profile(user_obj):
    return user_obj.profile.is_online


class ChatMessageBaseConsumer(AsyncWebsocketConsumer):
    groups = []
    user_group_list = []
    chat_obj = None
    user_obj = None

    async def message_send(self, event):
        data = {
            "updated_chat": event["updated_chat"],
            "user_status": event["user_status"],
            "message": event["message"],
            "action": event["action"],
        }
        await self.send(text_data=json.dumps(data))


class ChatMessagesConsumer(ChatMessageBaseConsumer):
    async def connect(self):
        chat_id = self.scope['url_route']['kwargs']['id']
        self.user_group_list.extend(self.groups)
        self.user_group_list.append(f"chat_{chat_id}")

        self.chat_obj = await get_chat(chat_id)
        self.user_obj = self.scope['user']

        if self.chat_obj and self.user_obj:
            await change_online_status(self.user_obj, True)
            for gp in self.user_group_list:
                await self.channel_layer.group_add(gp, self.channel_name)

            await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data = json.loads(text_data)
        except Exception as e:
            return e

        chat_data = await serialize_chat(self.chat_obj, self.user_obj)

        data = {
            "type": "message.send",
            "updated_chat": chat_data,
            "user_status": await get_user_profile(self.user_obj),
            "message": text_data.get("message", None),
            "action": text_data.get("action", "no_action"),
        }

        users = await get_chat_members(self.chat_obj)

        for uid in users:
            await self.channel_layer.group_send(uid, data)

    async def disconnect(self, code):
        if self.user_obj:
            await change_online_status(self.user_obj, False)

        for gp in self.user_group_list:
            await self.channel_layer.group_discard(gp, self.channel_name)


class ChatConsumer(ChatMessageBaseConsumer):
    async def connect(self):
        self.user_obj = self.scope['user']
        self.user_group_list.extend(self.groups)

        if self.user_obj:
            self.user_group_list.append(f"user_{self.user_obj.id}")
            await change_online_status(self.user_obj, True)

            await notify_user_friends(self, self.user_obj)

            for uid in self.user_group_list:
                await self.channel_layer.group_add(uid, self.channel_name)

            await self.accept()

    async def disconnect(self, code):
        if self.user_obj:
            await change_online_status(self.user_obj, False)
            await notify_user_friends(self, self.user_obj)

        for uid in self.user_group_list:
            await self.channel_layer.group_discard(uid, self.channel_name)
