from django.contrib.auth.models import User
from django.db import models

from main.models.base import BaseModel
from main.models.chat import Chat


class Video(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='all_videos')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_videos')
    video = models.FileField(upload_to='videos/')
    caption = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.video.name