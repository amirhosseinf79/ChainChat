from datetime import timedelta

from django.utils import timezone
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from ChainChat import settings


class BearerTokenAuthentication(authentication.TokenAuthentication):
    keyword = "Bearer"

    def authenticate_credentials(self, token):
        user, token = super().authenticate_credentials(token)
        if token.options.expiration_date and token.options.expiration_date < timezone.now():
            token.delete()
            raise AuthenticationFailed("Token has expired")

        return user, token