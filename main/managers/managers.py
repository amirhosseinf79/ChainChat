from django.db import models


class CustomManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class ChatManager(CustomManager):
    def create_private_chat(self, user1, user2):
        chat = self.create()
        chat.members.add(user1)
        chat.members.add(user2)
        return chat


class GroupManager(CustomManager):
    def create_group(self, name, user):
        obj = self.create(name=name)
        obj.admins.create(admin_id=user.id)
        obj.chat.members.create(member_id=user.id)
        return obj