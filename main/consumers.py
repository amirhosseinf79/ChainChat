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

@database_sync_to_async
def send_chat_members(self, chat_obj, data):
    chat_members = ChatMember.filtered_objects.filter(chat=chat_obj)
    for member in chat_members:
        self.channel_layer.group_send(f"user_{member.id}", data)

class ChatMessageBaseConsumer(AsyncWebsocketConsumer):
    groups = []
    user_group_list = []
    chat_obj = None
    user_obj = None

    async def message_send(self, event):
        data = {
            "updated_chat": event["updated_chat"],
            "message": event["message"],
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
        data = {
            "type": "message.send",
            "updated_chat": await serialize_chat(self.chat_obj, self.user_obj),
            "message": text_data,
        }

        send_chat_members(self, self.chat_obj, data)

        for gp in self.user_group_list:
            await self.channel_layer.group_send(gp, data)

    async def disconnect(self, code):
        if self.user_obj:
            await change_online_status(self.user_obj, False)

        for gp in self.user_group_list:
            await self.channel_layer.group_discard(gp, self.channel_name)


class ChatConsumer(ChatMessageBaseConsumer):
    async def connect(self):
        self.user_obj = self.scope['user']
        self.user_group_list.extend(self.groups)
        self.user_group_list.append(f"user_{self.user_obj.id}")

        if self.user_obj:
            await change_online_status(self.user_obj, True)
            for gp in self.user_group_list:
                await self.channel_layer.group_add(gp, self.channel_name)

            await self.accept()

    async def disconnect(self, code):
        if self.user_obj:
            await change_online_status(self.user_obj, False)

        for gp in self.user_group_list:
            await self.channel_layer.group_discard(gp, self.channel_name)
