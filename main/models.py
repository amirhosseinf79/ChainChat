from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from main.managers.managers import CustomManager, GroupManager, ChatManager, MessageManager


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return self.user.username


class BaseModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomManager()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    class Meta:
        abstract = True


class Group(BaseModel):
    name = models.CharField(max_length=120)
    invite_link = models.CharField(max_length=120, unique=True, blank=True, null=True)

    objects = GroupManager()

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

    def get_members(self, username=""):
        return self.members.filter(member__username__contains=username)

    def get_messages(self, user, msg_filter):
        if msg_filter:
            m_filter = Q(message__text__contains=msg_filter) or \
                       Q(video__caption__contains=msg_filter) or \
                       Q(photo__caption__contains=msg_filter)
        else:
            m_filter = Q()

        return self.chat_messagecontrollers.filter(chat__members__member=user).filter(m_filter)

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

    class Meta:
        abstract = True


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

    objects = MessageManager()


# Auto create profile
@receiver(post_save, sender=User)
def create_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)


# Auto create chat for group
@receiver(post_save, sender=Group)
def create_chat(sender, instance, **kwargs):
    Chat.objects.get_or_create(group=instance)


# Handle Messages by Signal
def update_controller(obj, instance):
    obj.is_deleted = instance.is_deleted
    obj.chat = instance.chat
    obj.author = instance.author
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

