from channels.auth import AuthMiddleware
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.sessions import CookieMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from rest_framework.authtoken.models import Token


@database_sync_to_async
def get_user(token):
    try:
        token = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return None

    return token.user


class QueryAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        token = scope.get("query_string", b"token=").decode("utf-8")
        token = token.replace("token=", "")
        scope['user'] = await get_user(token)
        return await super().__call__(scope, receive, send)