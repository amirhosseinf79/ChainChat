from django.db import models

from main.managers.managers import GroupManager
from main.models.base import BaseModel


class Group(BaseModel):
    name = models.CharField(max_length=120)
    invite_link = models.CharField(max_length=120, unique=True, blank=True, null=True)

    objects = GroupManager()

    def add_admin(self, user):
        self.admins.create(admin_id=user.id)

    def __str__(self):
        return self.name