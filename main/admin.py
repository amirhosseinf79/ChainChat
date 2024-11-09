from django.contrib import admin

from main.models import *


@admin.register(Chat)
class Chat(admin.ModelAdmin):
    list_display = ["id", "group", "created_at", "updated_at"]


@admin.register(ChatMember)
class ChatMember(admin.ModelAdmin):
    list_display = ("id", "chat", "member", "created_at", "updated_at")


@admin.register(Group)
class Group(admin.ModelAdmin):
    list_display = ["id", "name", "created_at", "updated_at"]


@admin.register(GroupAdmin)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "admin", "created_at", "updated_at")


@admin.register(Message)
class Message(admin.ModelAdmin):
    list_display = ("chat", "author", "created_at", "updated_at")


@admin.register(Photo)
class Photo(admin.ModelAdmin):
    list_display = ("chat", "author", "created_at", "updated_at")


# Register your models here.
@admin.register(Profile)
class Profile(admin.ModelAdmin):
    list_display = ["user", "phone_number"]
    list_filter = ["user__is_staff", "user__is_active"]
    search_fields = ["phone_number", "user__username"]


@admin.register(Video)
class Video(admin.ModelAdmin):
    list_display = ("chat", "author", "created_at", "updated_at")


@admin.register(MessageController)
class Video(admin.ModelAdmin):
    list_display = ("id", "chat", "author", "created_at", "updated_at")
