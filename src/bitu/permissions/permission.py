from typing import NewType, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.utils.module_loading import import_string
from .models import Permission, PermissionRequest, Log as PermissionLog

User = NewType('User', get_user_model())


class BaseBackend():
    """Base class for implementing new Permission backend.
    Each permission class must implement the methods defined in the base class.
    """

    def available_permissions(cls, user: 'User') -> list[Permission]:
        """Return a list of all permissions available to a given user.
        This should include all permissions that are currently pending approval.

        Backends may filter permissions returned based on their own internal logical.

        Args:
            user (User): Bitu User Object

        Raises:
            NotImplemented: Class does not implement this method

        Returns:
            list[Permission]: List of Permission types available for request.
        """
        raise NotImplementedError()

    def existing_permissions(cls, user: 'User') -> list[Permission]:
        """Return a list of all permissions currently assigned to a given user.

        Args:
            user (User):  Bitu User Object

        Raises:
            NotImplemented: Class does not implement this method

        Returns:
            list[Permission]: List of Permission type assigned to the given user.
        """
        raise NotImplementedError()

    def get_permission(cls, key: str) -> Union[Permission, None]:
        """Return a single permission by key.

        Args:
            key (str): Lookup key for backend system

        Raises:
            NotImplemented: Not implemented

        Returns:
            Permission: Single permission object or None
        """
        raise NotImplementedError()

    def get_pending(cls, user: 'User') -> QuerySet[PermissionRequest]:
        """Return any permissions pending approval from the user as a query set.

        Args:
            user (User): Bitu User Object

        Returns:
            QuerySet[PermissionRequest]: Django QuerySet for PermissionsRequest.
        """
        raise NotImplementedError()

    def grant(cls, user: 'User', permission: Permission):
        """Grant permission to user.

        Args:
            user (User): Bitu User Object
            permission (Permission): Bitu Permission Object

        Raises:
            NotImplemented: Not implemented
        """
        raise NotImplementedError()

class PermissionSet(BaseBackend):
    _backends = {}

    def __init__(self) -> None:
        for k, v in settings.BITU_SUB_SYSTEMS.items():
            if not v.get('permissions', False):
                continue

            self._backends[k] = import_string(v['permissions'])()

    def filter_permissions(self, permissions: list[Permission]) -> list[Permission]:
        filtered: list[Permission] = []
        for permission in permissions:
            if permission.source not in settings.ACCESS_REQUEST_RULES:
                continue
            if permission.key.lower() not in settings.ACCESS_REQUEST_RULES[permission.source]:
                continue
            filtered.append(permission)
        return filtered

    def available_permissions(self, user: 'User') -> list[Permission]:
        if not self._backends:
            raise RuntimeWarning("Attempting to list permissions with no backends configured")

        permissions = []
        [permissions.extend(b.available_permissions(user)) for b in self._backends.values()]
        return self.filter_permissions(permissions)

    def existing_permissions(self, user: 'User') -> list[Permission]:
        permissions = []
        [permissions.extend(b.existing_permissions(user)) for b in self._backends.values()]
        return self.filter_permissions(permissions)

    def get_permission(self, system: str, key: str) -> Union[Permission, None]:
        return self._backends[system].get_permission(key)

    def get_pending(self, user: User) -> QuerySet[PermissionRequest]:
        # Get all requests from all backends, which have us listed as an approver and
        # extact the IDs for those requests.
        requests = []
        [requests.extend(b.get_pending(user)) for b in self._backends.values()]
        ids = [request.id for request in requests]

        # Find any log object that we may already have created for any of the pending
        # requests. Once we've created a log entry, either by approving or rejecting a
        # request, we want that request to disappear from our list of pending requests.
        logs = PermissionLog.objects.filter(request__in=requests)

        # Get all the requests objects which we're allowed to approve, but exclude those
        # for which we already created a log entries. Note that we are also not allowed
        # to approve our own requests.
        return PermissionRequest.objects.filter(id__in=ids).exclude(log__in=logs).exclude(user=user)


permission_set = PermissionSet()
