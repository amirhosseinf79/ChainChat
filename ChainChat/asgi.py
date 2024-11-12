"""
ASGI config for ChainChat project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import CookieMiddleware, SessionMiddleware
from django.core.asgi import get_asgi_application

import main.ws_urls
from main.ws_middleware import QueryAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChainChat.settings')

application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': AllowedHostsOriginValidator(
                CookieMiddleware(
                    SessionMiddleware(
                        QueryAuthMiddleware(URLRouter(main.ws_urls.URL_PATTERNS))
                    )
                )
        )
    }
)
