from django.contrib.auth.models import User
from django.db import models

from main.models.base import BaseModel
from main.models.chat import Chat


class Photo(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='all_photos')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_photos')
    image = models.ImageField(upload_to='images/')
    caption = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.image.name