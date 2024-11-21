from django.utils import timezone

from rest_framework.permissions import DjangoModelPermissions
from rest_framework import generics

from .serializers import BlockListIPSerializer, UserValidationSerializer
from .models import BlockListIP, UserValidation


class BlocklistIPApiView(generics.ListAPIView):
    permission_classes = [DjangoModelPermissions]
    queryset = BlockListIP.objects.all()
    serializer_class = BlockListIPSerializer

    def get_queryset(self):
        ip = self.kwargs['ip']
        queryset = super().get_queryset().filter(expiry__gt=timezone.now())
        return queryset.filter(start__lte=ip, end__gte=ip)


class UsernameValidatorApiView(generics.CreateAPIView):
    """Takes a username, and an optional UID (shell account name) and returns
    the same data along with a sanitized version of the username, compatible
    with MediaWiki, if the username is valid.

    If the UID is excluded, the API will generate a suggestion, based on the
    supplied username.

    Return a HTTP 201 if the input is valid, HTTP 400 Bad request otherwise.
    """
    serializer_class = UserValidationSerializer
    queryset = UserValidation.objects.all()
