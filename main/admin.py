from django.contrib import admin

from main.models import *


@admin.register(ExpiringToken)
class ExpiringTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "token", "expiration_date")
    list_display_links = list_display


@admin.register(Chat)
class Chat(admin.ModelAdmin):
    list_display = ["id", "group", "created_at", "updated_at", "is_deleted"]
    list_display_links = list_display


@admin.register(ChatMember)
class ChatMember(admin.ModelAdmin):
    list_display = ("id", "chat", "member", "created_at", "updated_at", "is_deleted")
    list_display_links = list_display


@admin.register(Group)
class Group(admin.ModelAdmin):
    list_display = ["id", "name", "created_at", "updated_at", "is_deleted"]
    list_display_links = list_display


@admin.register(GroupAdmin)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "admin", "created_at", "updated_at", "is_deleted")
    list_display_links = list_display


@admin.register(Message)
class Message(admin.ModelAdmin):
    list_display = ("chat", "author", "created_at", "updated_at", "is_deleted", "delete_for_me")
    list_display_links = list_display


@admin.register(Photo)
class Photo(admin.ModelAdmin):
    list_display = ("chat", "author", "created_at", "updated_at", "is_deleted", "delete_for_me")
    list_display_links = list_display


@admin.register(Video)
class Video(admin.ModelAdmin):
    list_display = ("chat", "author", "created_at", "updated_at", "is_deleted", "delete_for_me")
    list_display_links = list_display


@admin.register(MessageController)
class MsgController(admin.ModelAdmin):
    list_display = ("id", "chat", "author", "created_at", "updated_at", "is_deleted", "delete_for_me")
    list_display_links = list_display


@admin.register(SeenUser)
class MsgController(admin.ModelAdmin):
    list_display = ("id", "message", "user", "created_at", "updated_at", "is_deleted")
    list_display_links = list_display


# Register your models here.
@admin.register(Profile)
class Profile(admin.ModelAdmin):
    list_display = ["user", "phone_number"]
    list_filter = ["user__is_staff", "user__is_active"]
    search_fields = ["phone_number", "user__username"]
    list_display_links = list_display


@admin.register(BlockedUser)
class Profile(admin.ModelAdmin):
    list_display = ["id", "blocked_by", "user", "created_at", "updated_at", "is_deleted"]
    search_fields = ["blocked_by__user__username", "user__user__username"]
    list_display_links = list_display