from django.urls import path

from main.views import ChatMessagesView, ChatMembersView, ChatListView, ChatDetailsView, CreateGroup, ChatCreateView, \
    JoinChatView, LeaveChatView, CreateMessageView, EditMessageView, DeleteMessageView, MessageReadView

urlpatterns = [
    path("group/create", CreateGroup.as_view(), name="create-group"),
    path("chat/create", ChatCreateView.as_view(), name="create-chat"),
    path("chat/getList", ChatListView.as_view(), name="get-all-chats"),
    path("chat/<int:pk>/", ChatDetailsView.as_view(), name="get-chats-details"),
    path("chat/<int:pk>/joinChat", JoinChatView.as_view(), name="join-chat"),
    path("chat/<int:pk>/leaveChat", LeaveChatView.as_view(), name="leave-chat"),
    path('chat/<int:pk>/getMessages', ChatMessagesView.as_view(), name='get-messages'),
    path('chat/<int:pk>/getMembers', ChatMembersView.as_view(), name='get-members'),
    path('chat/<int:pk>/createMessage', CreateMessageView.as_view(), name='create-message'),
    path('chat/<int:pk>/editMessage', EditMessageView.as_view(), name='edit-message'),
    path('chat/<int:pk>/markRead', MessageReadView.as_view(), name='mark-read-message'),
    path('chat/<int:pk>/deleteMessage', DeleteMessageView.as_view(), name='delete-message'),
]