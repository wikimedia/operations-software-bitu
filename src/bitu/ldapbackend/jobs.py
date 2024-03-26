# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from typing import Dict, NewType, TYPE_CHECKING

import bituldap

from django.conf import settings
from django.utils.timezone import localtime
from django_rq import job

from bitu import utils
from . import helpers
from .exceptions import UIDRangeException


if TYPE_CHECKING:
    from signups.models import Signup
    from keymanagement.models import SSHKey
    from django.contrib.auth import get_user_model
    User = NewType('User', get_user_model())

logger = logging.getLogger('bitu')


@job
def create_user(signup: 'Signup'):
    if bituldap.get_user(signup.uid):
        return True

    user = bituldap.new_user(signup.uid)

    try:
        user = helpers.default_ldap_user_data_fill(signup, user)
    except UIDRangeException as e:
        utils.send_service_message(
            'Error creating user',
            f"""Failed to allocate UID Number in LDAP, range violation.
            LDAP returned uid number in invalid range.
            Exception: {e}
            """)
        return False
    except Exception:
        return False

    success = user.entry_commit_changes()

    if success:
        try:
            add_to_default_groups(user.entry_dn)
        except Exception as exception:
            utils.send_service_message(
                'Error creating user',
                f"""Failed to add user: {signup.uid} to groups.
                exception was: {exception}
                """
            )
    else:
        # Error notification
        logger.error('Failed to create user %s' % signup.uid)
        utils.send_service_message('Error creating user',
                                   f"""Failed to create user: {signup.uid}""")

    utils.send_service_message(f'LDAP user created: {signup.uid}',
                               f"""New user created successfully by Bitu.\n\n
                               Username: {signup.username} as been created.\n
                               UID: {signup.uid}\n
                               Email: {signup.email}\n
                               Creation time: {localtime()}\n
                               Signup time: {signup.created_date}\n
                               """,
                               limited=True)
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
def update_ldap_attributes(user: 'User', attributes: Dict):
    ldap_user = bituldap.get_user(user.get_username())
    if not ldap_user:
        logger.warning(f'user: {user.get_username()} not found in ldap')
        return

    for k, v in attributes.items():
        setattr(ldap_user, k, v)
        ldap_user.entry_commit_changes()

    logger.info(f'update ldap user: {ldap_user} with attributes: {attributes}')


@job
def check_ssh_key(key: 'SSHKey'):
    ldap_user = bituldap.get_user(key.user.get_username())
    if key.key_as_byte_string in ldap_user.sshPublicKey:
        key.active = True
        key.system = __name__.split('.')[0]
        key.save()


@job
def update_ssh_key(key: 'SSHKey'):
    if not key.active:
        return

    ldap_user = bituldap.get_user(key.user.get_username())
    if key.key_as_byte_string not in ldap_user.sshPublicKey:
        ldap_user.sshPublicKey.add(key.key_as_byte_string)
        ldap_user.entry_commit_changes()


@job
def remove_ssh_key(key: 'SSHKey'):
    if key.active:
        return

    ldap_user = bituldap.get_user(key.user.get_username())
    ldap_user.sshPublicKey.delete(key.key_as_byte_string)
    ldap_user.entry_commit_changes()


@job
def syncronize_ssh_keys(user: 'User'):
    ldap_user = bituldap.get_user(user.get_username())
    for key in user.ssh_keys.all():
        if key.active and key.key_as_byte_string not in ldap_user.sshPublicKey:
            ldap_user.sshPublicKey.add(key.key_as_byte_string)
        elif not key.active and key.key_as_byte_string in ldap_user.sshPublicKey:
            ldap_user.sshPublicKey.delete(key.key_as_byte_string)
    ldap_user.entry_commit_changes()
    load_ssh_key(user)


@job
def load_ssh_key(user: 'User'):
    from keymanagement.models import SSHKey
    system = __name__.split('.')[0]

    ldap_user = bituldap.get_user(user.get_username())

    # Check if we have any keys that are listed as active, but not in LDAP.
    # LDAP is authoritive, so deactivate any keys not found.
    for key in user.ssh_keys.all():
        if key.active and key.key_as_byte_string not in ldap_user.sshPublicKey.values:
            key.active = False
            key.save()

        if not key.active:
            key.system = ''
            key.save()

    for key in ldap_user.sshPublicKey.values:
        ssh_key, created = SSHKey.objects.get_or_create(user=user, ssh_public_key=key.decode('utf-8'))

        if created:
            ssh_key.system = system
            ssh_key.comment = ''
            ssh_key.active = True
            ssh_key.key_type = ssh_key.get_key_type()
            ssh_key.key_size = ssh_key.get_key_length()
            ssh_key.save()
            continue

        # If a key already existed, then that key is active in LDAP and this state should be
        # reflected in Bitu.
        # DO NOT be tempted to remove the if-clause, it guards against endlessly looping as the
        # save signal on the key model is hooked up to this function.
        if not ssh_key.active:
            ssh_key.active = True
            ssh_key.save()
