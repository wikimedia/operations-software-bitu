# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from typing import Dict, NewType, TYPE_CHECKING

import bituldap

from django.conf import settings
from django_rq import job
from . import helpers
if TYPE_CHECKING:
    from signups.models import Signup
    from keymanagement.models import SSHKey
    from django.contrib.auth import get_user_model
    User = NewType('User', get_user_model())

logger = logging.getLogger('bitu')

@job
def create_user(signup: 'Signup'):
    uid = signup.username.lower()
    if bituldap.get_user(uid):
        return

    user = bituldap.new_user(uid)
    user = helpers.default_ldap_user_data_fill(signup, user)
    success = user.entry_commit_changes()

    if success:
        add_to_default_groups(user.entry_dn)

    return success


@job
def add_to_default_groups(user_dn):
    for group_name in settings.BITU_SUB_SYSTEMS['ldapbackend'].get('default_groups', []):
        group = bituldap.get_group(group_name)
        if not group:
            continue
        group.member.add(user_dn)
        group.entry_commit_changes()


@job
def update_ldap_attributes(user:'User', attributes:Dict):
    ldap_user = bituldap.get_user(user.get_username())
    if not ldap_user:
        logger.warning(f'user: {user.get_username()} not found in ldap')
        return

    for k,v in attributes.items():
        setattr(ldap_user, k, v)
        ldap_user.entry_commit_changes()

    logger.info(f'update ldap user: {ldap_user} with attributes: {attributes}')


@job
def check_ssh_key(key: 'SSHKey'):
    ldap_user = bituldap.get_user(key.user.get_username())
    if ldap_user.sshPublicKey == key.key_as_byte_string:
        key.active = True
        key.system = __name__.split('.')[0]
        key.save()


@job
def update_ssh_key(key: 'SSHKey'):
    if not key.active:
        return

    from keymanagement.models import SSHKey
    keys = SSHKey.objects.filter(system=key.system, user=key.user, active=True).exclude(pk=key.pk)
    for invalid in keys:
        invalid.active = False
        invalid.save()

    ldap_user = bituldap.get_user(key.user.get_username())
    ldap_user.sshPublicKey = key.ssh_public_key
    ldap_user.entry_commit_changes()

@job
def remove_ssh_key(key: 'SSHKey'):
    ldap_user = bituldap.get_user(key.user.get_username())
    if ldap_user.sshPublicKey == key.key_as_byte_string and not key.active:
        ldap_user.sshPublicKey = ''
        ldap_user.entry_commit_changes()

@job
def load_ssh_key(user: 'User'):
    from keymanagement.models import SSHKey
    system = __name__.split('.')[0]
    ldap_user = bituldap.get_user(user.get_username())

    ssh_key, created = SSHKey.objects.get_or_create(user=user,
                                           ssh_public_key=ldap_user.sshPublicKey.value.decode('utf-8'))
    if created:
        ssh_key.comment=f'Imported from {system}'

    ssh_key.active = True
    ssh_key.save()

