"""
ASGI config for ChainChat project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import CookieMiddleware, SessionMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChainChat.settings')

from main.ws_urls import URL_PATTERNS
from main.ws_middleware import QueryAuthMiddleware

application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': AllowedHostsOriginValidator(
                CookieMiddleware(
                    SessionMiddleware(
                        QueryAuthMiddleware(URLRouter(URL_PATTERNS))
                    )
                )
        )
    }
)
