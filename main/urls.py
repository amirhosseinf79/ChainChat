from django.urls import path

from main.api.genericViews.auth import AuthLoginView, AuthCreateUserView
from main.views import *

urlpatterns = [
    path("auth/info", GetMyInfo.as_view(), name="auth-info"),
    path("auth/login", AuthLoginView.as_view(), name="login"),
    path("auth/createAccount", AuthCreateUserView.as_view(), name="create-account"),
    path("group/create", CreateGroup.as_view(), name="create-group"),
    path("chat/create", ChatCreateView.as_view(), name="create-chat"),
    path("chat/getList", ChatListView.as_view(), name="get-all-chats"),
    path("chat/<int:pk>/", ChatDetailsView.as_view(), name="get-chats-details"),
    path("chat/joinChat", JoinChatView.as_view(), name="join-chat"),
    path("chat/<int:pk>/leaveChat", LeaveChatView.as_view(), name="leave-chat"),
    path('chat/<int:pk>/getMessages', ChatMessagesView.as_view(), name='get-messages'),
    path('chat/<int:pk>/getMembers', ChatMembersView.as_view(), name='get-members'),
    path('chat/<int:pk>/createMessage', CreateEditMessageView.as_view(), name='create-message'),
    path('chat/<int:pk>/markRead', MessageReadView.as_view(), name='mark-read-message'),
    path('chat/<int:pk>/deleteMessage', DeleteMessageView.as_view(), name='delete-message'),
    path('user/getList', GetUsersListView.as_view(), name='get-users-list'),
    path('user/<int:pk>/', GetUserDetailsView.as_view(), name='get-user-details'),
    path('user/<int:pk>/blockUser', BlockUserView.as_view(), name='block-user'),
    path('user/<int:pk>/unblockUser', UnblockUserView.as_view(), name='unblock-user'),
]