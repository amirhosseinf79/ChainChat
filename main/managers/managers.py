from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q


class FilteredManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class ChatManager(models.Manager):
    def create_private_chat(self, me, user):
        if me and user and me != user:
            user1 = User.objects.filter(id=me)
            user2 = User.objects.filter(id=user)

            if user1.count() > 0 and user2.count() > 0:
                chat_ins = self.filter(members__member_id=me).filter(members__member_id=user) \
                    .filter(group__isnull=True).distinct()

                if chat_ins.exists():
                    chat = chat_ins.first()
                    obj, created = chat.members.get_or_create(member_id=me)
                    obj.is_deleted = False
                    obj.save()

                    obj, created = chat.members.get_or_create(member_id=user)
                    obj.is_deleted = False
                    obj.save()
                else:
                    chat = self.create()
                    chat.members.create(member_id=me)
                    chat.members.create(member_id=user)

                return chat

        return None

    def find_chat(self, title):
        query = (Q(group__isnull=False) & Q(group__name__contains=title)) | \
                (Q(group__isnull=True) & (Q(members__member__username__contains=title) |
                                          Q(members__member__first_name__contains=title)))

        obj_list = self.filter(query).distinct()
        return obj_list

class GroupManager(models.Manager):
    def create_group(self, name, user):
        obj = self.create(name=name)
        obj.admins.create(admin_id=user.id)
        obj.chat.members.create(member_id=user.id)
        return obj


class FilteredChatManager(ChatManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class FilteredGroupManager(GroupManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)