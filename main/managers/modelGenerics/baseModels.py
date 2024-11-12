from django.contrib.auth.models import User
from django.db import models

from main.managers.managers import FilteredManager, MessageManager, FilteredMessageManager


class BaseModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    filtered_objects = FilteredManager()

    def mark_delete(self):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True


class BaseMessage(BaseModel):
    chat = models.ForeignKey("Chat", null=True, blank=True, on_delete=models.CASCADE, related_name='chat_%(class)ss')
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='user_%(class)ss')
    edited_at = models.DateTimeField(null=True, blank=True)
    delete_for_me = models.BooleanField(default=False)
    reply = models.ForeignKey("MessageController", null=True, blank=True, on_delete=models.CASCADE, related_name='reply_%(class)ss')

    objects = MessageManager()
    filtered_objects = FilteredMessageManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']