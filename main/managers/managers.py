from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.http import Http404


class FilteredManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class ChatManager(models.Manager):
    def create_private_chat(self, user, start_with):
        if user and start_with and user != start_with:
            user1 = User.objects.filter(id=user)
            user2 = User.objects.filter(id=start_with)

            if user1.count() > 0 and user2.count() > 0:
                chat_ins = self.filter(members__member_id=user).filter(members__member_id=start_with) \
                    .filter(group__isnull=True).distinct()

                if chat_ins.exists():
                    chat = chat_ins.first()
                    obj, created = chat.members.get_or_create(member_id=user)
                    if obj.is_deleted:
                        obj.is_deleted = False
                        obj.save()

                    obj, created = chat.members.get_or_create(member_id=start_with)
                    obj.is_deleted = False
                    obj.save()
                else:
                    chat = self.create()
                    chat.members.create(member_id=user)
                    chat.members.create(member_id=start_with)

                return chat

        return None

    def find_chat(self, title):
        query = (Q(group__isnull=False) & Q(group__name__contains=title)) | \
                (Q(group__isnull=True) & (Q(members__member__username__contains=title) |
                                          Q(members__member__first_name__contains=title) |
                                          Q(members__member__last_name__contains=title)
                                          ))

        obj_list = self.filter(query).distinct()
        return obj_list


class FilteredChatManager(ChatManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class GroupManager(models.Manager):
    def create_group(self, name, user, invite_link):
        obj = self.create(name=name, invite_link=invite_link)
        obj.admins.create(admin_id=user)
        obj.chat.members.create(member_id=user)
        return obj


class FilteredGroupManager(GroupManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class MessageManager(models.Manager):
    def create_message(self, chat_id, author, **kwargs):
        return self.create(chat_id=chat_id, author=author, **kwargs)

    def edit_message(self, message_id, chat_id, author, **kwargs):
        self.filter(id=message_id).update(author=author, chat_id=chat_id, **kwargs)
        return None

    def delete_message(self, message_id, chat_id, author_id, for_everyone=False):
        try:
            obj = self.get(chat_id=chat_id, author_id=author_id, id=message_id)
        except ObjectDoesNotExist:
            raise Http404

        if for_everyone:
            obj.mark_delete()
        else:
            obj.delete_for_me = True
            obj.save()

        return None


class FilteredMessageManager(MessageManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class MessageControlManager(MessageManager):
    def mark_seen(self, chat_id, author_id, user_id, message_id):
        unread_messages = self.filter(chat_id=chat_id, id__lte=message_id) \
            .exclude(author_id=author_id).exclude(seen_users__user_id=user_id)

        for message in unread_messages:
            message.seen_users.update_or_create(user_id=user_id)

        return None

class FilteredMessageControlManager(MessageManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
