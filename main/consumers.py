import json
import time
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
def get_user_chats(user_obj):
    return ChatMember.filtered_objects.filter(member=user_obj).values_list("chat_id", flat=True).distinct()

@database_sync_to_async
def change_online_status(user_obj, is_online):
    user_obj.profile.is_online = is_online
    return user_obj.profile.save()

@database_sync_to_async
def get_user_profile(user_obj):
    return user_obj.profile.is_online


class ChatMessageBaseConsumer(AsyncWebsocketConsumer):
    groups = []
    user_group_list = {}
    chat_obj = None
    user_obj = None

    async def notify_user_friends(self, user_status):
        user_name = f"user_{self.user_obj.id}"
        chats = await get_user_chats(self.user_obj)
        async for chat in chats:
            chat_obj = await get_chat(chat)
            chat_name = f"chat_{chat}"

            if chat_name in self.user_group_list:
                if user_name not in self.user_group_list[chat_name]:
                    self.user_group_list[chat_name].append(user_name)

                sent = []
                for user in self.user_group_list[chat_name]:
                    if user not in sent:
                        if user != user_name:
                            data = {
                                "type": "message.send",
                                "updated_chat": await serialize_chat(chat_obj, self.user_obj),
                                "user_status": user_status,
                                "message": None,
                                "action": "online_status",
                            }
                            sent.append(user)
                            print(user)
                            await self.channel_layer.group_send(user, data)
            else:
                self.user_group_list[chat_name] = [user_name]

    async def message_send(self, event):
        data = {
            "updated_chat": event["updated_chat"],
            "user_status": event["user_status"],
            "message": event["message"],
            "action": event["action"],
            "time": time.time(),
        }
        await self.send(text_data=json.dumps(data))


class ChatMessagesConsumer(ChatMessageBaseConsumer):
    async def connect(self):
        chat_id = self.scope['url_route']['kwargs']['id']
        self.chat_obj = await get_chat(chat_id)
        self.user_obj = self.scope['user']

        if self.chat_obj and self.user_obj:
            chat_name = f"chat_{chat_id}"
            user_name = f"user_{self.user_obj.id}"

            if chat_name in self.user_group_list:
                if user_name not in self.user_group_list[chat_name]:
                    self.user_group_list[chat_name].append(user_name)
            else:
                self.user_group_list[chat_name] = [f"user_{self.user_obj}"]
                await change_online_status(self.user_obj, True)

            await self.channel_layer.group_add(user_name, self.channel_name)

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

        chat_name = f"chat_{self.chat_obj.id}"
        if chat_name in self.user_group_list:
            for user in self.user_group_list[chat_name]:
                await self.channel_layer.group_send(user, data)

    async def disconnect(self, code):
        if self.user_obj:
            await change_online_status(self.user_obj, False)
            await self.channel_layer.group_discard(f"user_{self.user_obj.id}", self.channel_name)


class ChatConsumer(ChatMessageBaseConsumer):
    async def connect(self):
        self.user_obj = self.scope['user']
        print(self.user_group_list)

        if self.user_obj:
            await self.notify_user_friends(True)
            user_name = f"user_{self.user_obj.id}"
            await change_online_status(self.user_obj, True)
            await self.channel_layer.group_add(user_name, self.channel_name)
            await self.accept()

    async def disconnect(self, code):
        if self.user_obj:
            await self.notify_user_friends(False)
            await change_online_status(self.user_obj, False)
            await self.channel_layer.group_discard(f"user_{self.user_obj.id}", self.channel_name)
