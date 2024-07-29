from rest_framework import authentication

from accounts.models import Token


class BituTokenAuthentication(authentication.TokenAuthentication):
    model = Token
