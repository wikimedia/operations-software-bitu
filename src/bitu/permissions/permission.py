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

    def filter_permissions(self, permissions: list[Permission], user: 'User') -> list[Permission]:
        filtered: list[Permission] = []
        for permission in permissions:
            if not permission.configured:
                continue
            if not permission.run_validators(user):
                continue
            filtered.append(permission)
        return filtered

    def available_permissions(self, user: 'User') -> list[Permission]:
        if not self._backends:
            raise RuntimeWarning("Attempting to list permissions with no backends configured")

        permissions = []
        [permissions.extend(b.available_permissions(user)) for b in self._backends.values()]
        return self.filter_permissions(permissions, user)

    def existing_permissions(self, user: 'User') -> list[Permission]:
        permissions = []
        [permissions.extend(b.existing_permissions(user)) for b in self._backends.values()]
        return self.filter_permissions(permissions, user)

    def get_permission(self, system: str, key: str) -> Union[Permission, None]:
        return self._backends[system].get_permission(key)

    def get_pending(self, user: User) -> QuerySet[PermissionRequest]:
        # Find all the rules which require approval of a manager and extract the id of
        # the pending PermissionRequest for that permission.
        requests = []
        for system, rule_sets in settings.ACCESS_REQUEST_RULES.items():
            for key, rules in rule_sets.items():
                for rule in rules:
                    if user.get_username() in rule.get('managers', []):
                        requests.extend(PermissionRequest.objects.filter(system=system, key=key, status=PermissionRequest.PENDING).values_list('id', flat=True))

        # Get all the log objects for the current pending requests made by the current user.
        # Use the list of logs to exclude permissions we already approved and add an exclude to
        # remove any requests made by the user.
        logs = PermissionLog.objects.filter(request__id__in=requests, created_by=user)
        return PermissionRequest.objects.filter(id__in=requests).exclude(log__in=logs).exclude(user=user)


permission_set = PermissionSet()
