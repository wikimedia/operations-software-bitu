
from typing import NewType, TYPE_CHECKING, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string
from .models import Permission

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
        raise NotImplemented()
    
    def existing_permissions(cls, user: 'User') -> list[Permission]:
        """Return a list of all permissions currently assigned to a given user.

        Args:
            user (User):  Bitu User Object

        Raises:
            NotImplemented: Class does not implement this method

        Returns:
            list[Permission]: List of Permission type assigned to the given user.
        """
        raise NotImplemented()

    def get_permission(cls, key:str) -> Union[Permission, None]:
        """Return a single permission by key.

        Args:
            key (str): Lookup key for backend system

        Raises:
            NotImplemented: Not implemented

        Returns:
            Permission: Single permission object or None
        """
        raise NotImplemented


class PermissionSet(BaseBackend):
    _backends = {}

    def __init__(self) -> None:
        for k, v in settings.BITU_SUB_SYSTEMS.items():
            if not v.get('permissions', False):
                continue

            self._backends[k] = import_string(v['permissions'])()

    def available_permissions(self, user: 'User') -> list[Permission]:
        permissions = []
        [permissions.extend(b.available_permissions(user)) for b in self._backends.values()]
        return permissions

    def existing_permissions(self, user: 'User') -> list[Permission]:
        permissions = []
        [permissions.extend(b.existing_permissions(user)) for b in self._backends.values()]
        return permissions

    def get_permission(self, system: str, key: str) -> Union[Permission, None]:
        return self._backends[system].get_permission(key)
