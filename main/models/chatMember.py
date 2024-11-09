from django.contrib.auth.models import User
from django.db import models

from main.models.base import BaseModel
from main.models.chat import Chat


class ChatMember(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='members')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_chats')

    class Meta:
        unique_together = (('chat', 'member'),)

    def __str__(self):
        return f"{self.id}"