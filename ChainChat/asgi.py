"""
ASGI config for ChainChat project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChainChat.settings')

time.sleep(5)

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import CookieMiddleware, SessionMiddleware
from django.core.asgi import get_asgi_application

import main.ws_urls
from main.ws_middleware import QueryAuthMiddleware

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
