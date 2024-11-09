from django.contrib.auth.models import User
from django.db import models

from main.models.base import BaseModel
from main.models.chat import Chat


class Message(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='all_messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='u_messages')
    text = models.TextField()

    def __str__(self):
        return self.text