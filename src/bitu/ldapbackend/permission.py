from typing import Union

import bituldap

from ldap3 import Entry

from permissions.models import Permission, PermissionRequest
from permissions.permission import BaseBackend, User


class LDAPPermissions(BaseBackend):
    def __init__(self) -> None:
        self._my_permissions: list[Permission] = []
        self._permissions: list[Permission] = []

    def get_state(self, user, entry: Entry):
        try:
            pr = PermissionRequest.objects.get(user=user, system='ldapbackend', key=entry.entry_dn)
            return pr.status
        except PermissionRequest.DoesNotExist:
            return PermissionRequest.SYNCRONIZED

    def _entries_to_permission_list(self, user: User, entries: list[Entry]) -> list[Permission]:
        perms: list[Permission] = []
        for entry in entries:
            perms.append(Permission(
                key=entry.entry_dn,
                name=entry.cn,
                description=entry.description if entry.description else '',
                source='ldapbackend',
                source_display='LDAP',
                owners=entry.owner,
                user=user,
                state=self.get_state(user, entry)
            ))
        return perms

    def get_permission(self, key) -> Union[Permission, None]:
        permissions = bituldap.list_groups()  # bituldap.list_groups(query='owner: *')
        for entry in permissions:
            if key == entry.entry_dn:
                return Permission(
                    key=entry.entry_dn,
                    name=entry.cn,
                    description=entry.description if entry.description else '',
                    source='ldapbackend',
                    source_display='LDAP',
                    owners=entry.owner,
                    state=PermissionRequest.SYNCRONIZED
                )
        return None


    def available_permissions(self, user: User) -> list[Permission]:
        existing = [p.key for p in self.existing_permissions(user)]
        available = []

        for group in bituldap.list_groups(query='owner: *'):
            if group.entry_dn not in existing:
                available.append(group)

        return self._entries_to_permission_list(user, available)


    def existing_permissions(self, user: User) -> list[Permission]:
        if self._my_permissions:
            return self._my_permissions
        ldap_user = bituldap.get_user(user.get_username())
        self._my_permissions = self._entries_to_permission_list(user, bituldap.member_of(ldap_user.entry_dn))
        return self._my_permissions