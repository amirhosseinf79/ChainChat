from django.contrib.auth.models import User
from django.db import models

from main.models.base import BaseModel
from main.models.group import Group


class GroupAdmin(BaseModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='admins')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_groups')

    class Meta:
        unique_together = (('group', 'admin'),)

    def __str__(self):
        return self.group.name