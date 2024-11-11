from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import Http404
from django.utils import timezone
from rest_framework.authtoken.models import Token

from ChainChat import settings
from main.managers.managers import FilteredManager, GroupManager, ChatManager, FilteredChatManager, \
    FilteredGroupManager, MessageManager, FilteredMessageManager


class ExpiringToken(models.Model):
    token = models.OneToOneField(Token, on_delete=models.CASCADE, related_name='options')
    expiration_date = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return self.expiration_date < timezone.now()

    def refresh(self):
        self.save()

    def save(self, *args, **kwargs):
        if not self.expiration_date and settings.TOKEN_EXPIRE_TIME:
            self.expiration_date = timezone.now() + timedelta(minutes=settings.TOKEN_EXPIRE_TIME)
        return super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=10, unique=True, blank=True, null=True)

    def block_list(self):
        obj = self.blocked_users.filter(is_deleted=False).distinct()
        return obj

    def is_blocked(self, block_by):
        return self.blocked_by_users.filter(blocked_by_id=block_by, is_deleted=False).exists()

    def block(self, block_by):
        obj = self.blocked_by_users.filter(blocked_by_id=block_by)

        if not obj:
            obj = self.blocked_by_users.create(blocked_by_id=block_by)
        else:
            obj.update(blocked_by_id=block_by, is_deleted=False)

        return obj

    def unblock(self, block_by):
        try:
            obj = self.blocked_by_users.get(blocked_by_id=block_by)
            obj.delete()
            return obj
        except ObjectDoesNotExist:
            raise Http404

    def __str__(self):
        return self.user.username


class BaseModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    filtered_objects = FilteredManager()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True


class BlockedUser(BaseModel):
    blocked_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='blocked_users')
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='blocked_by_users')

    class Meta:
        unique_together = (('user', 'blocked_by'),)


class Group(BaseModel):
    name = models.CharField(max_length=120)
    invite_link = models.CharField(max_length=120, unique=True, blank=True, null=True)

    objects = GroupManager()
    filtered_objects = FilteredGroupManager()

    def add_admin(self, user):
        self.admins.create(admin_id=user.id)

    def __str__(self):
        return self.name


class GroupAdmin(BaseModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='admins')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_groups')

    class Meta:
        unique_together = (('group', 'admin'),)

    def __str__(self):
        return self.group.name


class Chat(BaseModel):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='chat')

    objects = ChatManager()
    filtered_objects = FilteredChatManager()

    def join_chat(self, user):
        if self.group:
            obj, created = ChatMember.objects.get_or_create(member=user, chat=self)
            if not created:
                if obj.is_deleted:
                    obj.is_deleted = False
                    obj.save()
                else:
                    return False, "User already joined."

            return True, "User joined."
        else:
            return False, "Can't join private chat."

    def leave_chat(self, user):
        try:
            obj = ChatMember.objects.get(member=user, chat=self)
            if not obj.is_deleted:
                obj.is_deleted = True
                obj.save()
                return True, "User left."
            else:
                return False, "User already left."
        except ChatMember.DoesNotExist:
            return False, "Chat does not exist."

    def get_members(self, query=""):
        u_filter = Q(member__username__contains=query) | \
                   Q(member__first_name__contains=query) | \
                   Q(member__last_name__contains=query)

        return self.members.filter(u_filter).distinct()

    def get_messages(self, user, msg_filter="", date_filter=None):
        if msg_filter:
            m_filter = Q(message__text__contains=msg_filter) | \
                       Q(video__caption__contains=msg_filter) | \
                       Q(photo__caption__contains=msg_filter)
        else:
            m_filter = Q()

        d_filter = Q()

        if date_filter:
            from_date = date_filter.get("from_date", None)
            to_date = date_filter.get("to_date", None)
            d_filter &= Q(created_at__gte=from_date) if from_date else Q()
            d_filter &= Q(created_at__lte=to_date) if to_date else Q()

        hide_for_me = Q(delete_for_me=False) | ~Q(author=user)

        return self.chat_messagecontrollers \
                .filter(chat__members__member=user, ) \
                .filter(m_filter).filter(d_filter).filter(hide_for_me).distinct()

    def delete_chat(self, user):
        try:
            member_obj = self.members.get(member=user)
        except Chat.DoesNotExist:
            return False

        member_obj.is_deleted = True
        member_obj.save()
        return True

    class Meta:
        ordering = ("-updated_at", )

    def __str__(self):
        return f"{self.id}"


class ChatMember(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='members')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_chats')

    class Meta:
        unique_together = (('chat', 'member'),)

    def __str__(self):
        return f"{self.id}"


class BaseMessage(BaseModel):
    chat = models.ForeignKey(Chat, null=True, blank=True, on_delete=models.CASCADE, related_name='chat_%(class)ss')
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='user_%(class)ss')
    edited_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    delete_for_me = models.BooleanField(default=False)
    reply = models.ForeignKey("MessageController", null=True, blank=True, on_delete=models.CASCADE, related_name='reply_%(class)ss')

    objects = MessageManager()
    filtered_objects = FilteredMessageManager()

    class Meta:
        abstract = True
        ordering = ['-created_at']


class Message(BaseMessage):
    text = models.TextField()

    def __str__(self):
        return self.text


class Photo(BaseMessage):
    image = models.ImageField(upload_to='media/images/')
    caption = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.image.name


class Video(BaseMessage):
    video = models.FileField(upload_to='media/videos/')
    caption = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.video.name


class MessageController(BaseMessage):
    video = models.OneToOneField(
        Video,
        on_delete=models.CASCADE,
        related_name='video_messages',
        null=True,
        blank=True,
    )

    photo = models.OneToOneField(
        Photo,
        on_delete=models.CASCADE,
        related_name='photo_messages',
        null=True,
        blank=True,
    )

    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True,
    )

    def __str__(self):
        value = ""
        if self.video:
            value = "video"
        elif self.photo:
            value = "photo"
        elif self.message:
            value = self.message.text

        return value


# define Expire token date obj
@receiver(post_save, sender=Token)
def create_token(sender, instance, **kwargs):
    ExpiringToken.objects.update_or_create(token=instance)


# Auto create profile
@receiver(post_save, sender=User)
def create_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)

# Auto create chat for group
@receiver(post_save, sender=Group)
def create_chat(sender, instance, **kwargs):
    Chat.objects.get_or_create(group=instance)

# auto chat update_at handle
@receiver(post_save, sender=ChatMember)
def update_time(sender, instance, **kwargs):
    instance.chat.save()

# Handle Messages by Signal
def update_controller(obj, instance):
    obj.is_deleted = instance.is_deleted
    obj.chat = instance.chat
    obj.author = instance.author
    obj.delete_for_me = instance.delete_for_me
    obj.seen_at = instance.seen_at
    obj.edited_at = instance.edited_at
    obj.reply = instance.reply
    instance.chat.save()
    obj.save()

@receiver(post_save, sender=Message)
def create_message(sender, instance, **kwargs):
    obj, created = MessageController.objects.update_or_create(message_id=instance.id)
    update_controller(obj, instance)

@receiver(post_save, sender=Photo)
def create_photo(sender, instance, **kwargs):
    obj, created = MessageController.objects.update_or_create(photo_id=instance.id)
    update_controller(obj, instance)

@receiver(post_save, sender=Video)
def create_video(sender, instance, **kwargs):
    obj, created = MessageController.objects.update_or_create(video_id=instance.id)
    update_controller(obj, instance)
