import logging

from typing import Union

import bituldap

from django.conf import settings
from ldap3 import ObjectDef, Entry, Reader, Writer

from permissions.models import Permission, PermissionRequest
from permissions.permission import BaseBackend, User


logger = logging.getLogger('bitu')


class LDAPPermissions(BaseBackend):
    name = 'ldapbackend'

    def __init__(self) -> None:
        self._groups = []

    @property
    def groups(self):
        if self._groups:
            return self._groups

        keys = settings.ACCESS_REQUEST_RULES.get(self.name, {}).keys()
        for key in keys:
            self._groups.extend(self._get_groups_by_dn(key, attributes=['cn', 'owner', 'description']))
        return self._groups

    def _get_groups_by_dn(self, dn, attributes=[]):
        bound, connection = bituldap.create_connection()
        if not bound:
            return []

        config = bituldap.read_configuration()
        group = ObjectDef(config.groups.object_classes,
                      connection,
                      auxiliary_class=config.groups.auxiliary_classes)
        reader = Reader(connection, group, dn, 'cn: *', attributes=attributes)
        reader.search()
        return reader

    def _get_group_by_dn(self, dn, attributes=[]):
        reader = self._get_groups_by_dn(dn, attributes)

        # Convert to a writer, so that we can add new members
        # to the entry.
        writer = Writer.from_cursor(reader)

        # There should be only one group, nor none, as DNs are unique.
        for group in writer:
            if group.entry_dn == dn:
                return group
        return None

    def get_state(self, user, entry: Entry):
        pr = PermissionRequest.objects.filter(
            user=user,
            system=self.name,
            key=entry.entry_dn.__str__()).order_by('-created').first()
        if pr is None:
            return PermissionRequest.SYNCRONIZED
        return pr.status

    def _entries_to_permission_list(self, user: User, entries: list[Entry]) -> list[Permission]:
        perms: list[Permission] = []
        for entry in entries:
            perms.append(Permission(
                key=entry.entry_dn,
                name=entry.cn.__str__(),
                description=entry.description if entry.description else '',
                source=self.name,
                source_display='LDAP',
                owners=entry.owner,
                user=user,
                state=self.get_state(user, entry)
            ))
        return perms

    def get_permission(self, key) -> Union[Permission, None]:
        permissions = self._get_groups_by_dn(key)
        for entry in permissions:
            if key == entry.entry_dn:
                return Permission(
                    key=entry.entry_dn,
                    name=entry.cn.__str__(),
                    description=entry.description if entry.description else '',
                    source=self.name,
                    source_display='LDAP',
                    owners=entry.owner,
                    state=PermissionRequest.SYNCRONIZED
                )
        return None

    def available_permissions(self, user: User) -> list[Permission]:
        existing = [p.key for p in self.existing_permissions(user)]
        available = []

        for group in self.groups:
            if group.entry_dn not in existing:
                available.append(group)

        return self._entries_to_permission_list(user, available)

    def existing_permissions(self, user: User) -> list[Permission]:
        ldap_user = bituldap.get_user(user.get_username())
        return self._entries_to_permission_list(user, bituldap.member_of(ldap_user.entry_dn))

    def grant(self, user: User, permission: Permission):
        if permission.source != self.name:
            # Permission does not belong to this backend.
            return

        ldap_user = bituldap.get_user(user.get_username())
        groups = bituldap.member_of(ldap_user.entry_dn)

        if permission.key in [g.entry_dn for g in groups]:
            # Already have permission.
            return

        group = self._get_group_by_dn(permission.key, attributes=['cn'])
        if not group:
            logger.warning(f'Attempting to add user to non-existing group, system={self.name}, user:{user.get_username()}, group: {permission.key}')
            return
        group.member.add(ldap_user.entry_dn)
        group.entry_commit_changes()
        logger.info(f'Add user to group, system={self.name}, user:{user.get_username()}, group: {permission.key}')
