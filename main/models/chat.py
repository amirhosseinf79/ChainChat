from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from main.managers.managers import ChatManager
from main.models.group import Group
from main.models.base import BaseModel


class Chat(BaseModel):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='chat')

    objects = ChatManager()

    def __str__(self):
        return f"{self.id}"


@receiver(post_save, sender=Group)
def create_chat(sender, instance, **kwargs):
    Chat.objects.get_or_create(group=instance)