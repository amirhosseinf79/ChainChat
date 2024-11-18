from django.urls import path

from main.consumers import ChatMessagesConsumer, ChatConsumer

URL_PATTERNS = [
    path("ws/chat/<int:id>/", ChatMessagesConsumer.as_asgi(), name="ws-chat"),
    path("ws/chat/", ChatConsumer.as_asgi(), name="ws-chat-update"),
]