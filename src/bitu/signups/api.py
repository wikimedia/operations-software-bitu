from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import DjangoModelPermissions
from rest_framework import generics

from .serializers import UserValidationSerializer
from .models import UserValidation


class UsernameValidatorApiView(generics.CreateAPIView):
    """Takes a username, and an optional UID (shell account name) and returns
    the same data along with a sanitized version of the username, compatible
    with MediaWiki, if the username is valid.

    If the UID is excluded, the API will generate a suggestion, based on the
    supplied username.

    Return a HTTP 201 if the input is valid, HTTP 400 Bad request otherwise.
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [DjangoModelPermissions]
    serializer_class = UserValidationSerializer
    queryset = UserValidation.objects
