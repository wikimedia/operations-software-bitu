from typing import Union

import bituldap

from ldap3 import Entry

from permissions.models import Permission, PermissionRequest
from permissions.permission import BaseBackend, User


class LDAPPermissions(BaseBackend):
    def get_state(self, user, entry: Entry):
        pr = PermissionRequest.objects.filter(
            user=user,
            system='ldapbackend',
            key=entry.entry_dn).order_by('-created').first()
        if pr is None:
            return PermissionRequest.SYNCRONIZED
        return pr.status

    def _entries_to_permission_list(self, user: User, entries: list[Entry]) -> list[Permission]:
        perms: list[Permission] = []
        for entry in entries:
            perms.append(Permission(
                key=entry.entry_dn.__str__(),
                name=entry.cn.__str__(),
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
                    key=entry.entry_dn.__str__(),
                    name=entry.cn.__str__(),
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

        for group in bituldap.list_groups():
            if group.entry_dn not in existing:
                available.append(group)

        return self._entries_to_permission_list(user, available)

    def existing_permissions(self, user: User) -> list[Permission]:
        ldap_user = bituldap.get_user(user.get_username())
        return self._entries_to_permission_list(user, bituldap.member_of(ldap_user.entry_dn))

    def get_pending(self, user: User) -> list[Permission]:
        groups = bituldap.list_groups()
        requests = PermissionRequest.objects.filter(key__in=[group.entry_dn for group in groups], system='ldapbackend')
        return requests

    def grant(cls, user: User, permission: Permission):
        if permission.source != 'ldapbackend':
            # Permission does not belong to this backend.
            return

        ldap_user = bituldap.get_user(user.get_username())
        groups = bituldap.member_of(ldap_user.entry_dn)

        if permission.key in [g.entry_dn for g in groups]:
            # Already have permission.
            return

        group = bituldap.get_group(permission.name)
        group.member.add(ldap_user.entry_dn)
        group.entry_commit_changes()
