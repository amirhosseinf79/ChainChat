from django.urls import path



def get_asgi_urls():
    from main.consumers import ChatMessagesConsumer, ChatConsumer

    patterns = [
        path("ws/chat/<int:id>/", ChatMessagesConsumer.as_asgi(), name="ws-chat"),
        path("ws/chat/", ChatConsumer.as_asgi(), name="ws-chat-update"),
    ]
    return patterns