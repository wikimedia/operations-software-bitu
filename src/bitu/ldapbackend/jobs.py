# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from typing import Dict, NewType, TYPE_CHECKING

import bituldap

from django.conf import settings
from django.utils.timezone import localtime
from django_rq import job
from sshpubkeys import SSHKey as SSHPublicKey

from bitu import utils
from . import helpers
from .exceptions import UIDRangeException


if TYPE_CHECKING:
    from signups.models import Signup
    from keymanagement.models import SSHKey
    from django.contrib.auth import get_user_model
    User = NewType('User', get_user_model())

logger = logging.getLogger('bitu')
system = __name__.split('.')[0]


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
        logger.warning(
            f'failed to update user attributes, user not found in LDAP, user={user.get_username()},\
attributes={attributes}')
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
        key.system = system
        if not key.comment:
            comment = helpers.get_comment_from_imported_ssh_key(key.key_as_byte_string)
            key.comment = comment if comment else f'Imported from {key.get_system_display()}'
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
    for k in ldap_user.sshPublicKey:
        ssh_public_key = SSHPublicKey(keydata=k.decode('utf8'))
        if ssh_public_key.hash_sha512() == key.get_finger_print():
            ldap_user.sshPublicKey.delete(k)
            ldap_user.entry_commit_changes()


def push_ssh_key(key: 'SSHKey'):
    # Key is not relevant for this backend or not active.
    if key.system != system or not key.active:
        return

    # Check if the key already exists in LDAP and only add if finger print is not found.
    ldap_user = bituldap.get_user(key.user.get_username())
    finger_prints = [SSHPublicKey(keydata=k.decode('utf8')).hash_sha512() for k in ldap_user.sshPublicKey]
    if key.get_finger_print() in finger_prints:
        return

    ldap_user.sshPublicKey.add(key.key_as_byte_string)
    ldap_user.entry_commit_changes()


@job
def syncronize_ssh_keys(user: 'User'):
    ldap_user = bituldap.get_user(user.get_username())

    # Remove all key which have been marked as inactive from LDAP.
    # Because LDAP is less restrictive than Bitu in regards to whitespace and newlines,
    # loop through all the keys stored in LDAP and check if it matches an inactive key
    # in the Bitu database. Note that if the user SHOULD somehow have duplicate keys in
    # Bitu, either can trigger a removal in LDAP. The key removed from LDAP MUST be the
    # key as returned from LDAP as the cleaned up version stored in Bitu will not match
    # and the key will therefor not be removed.
    for key in ldap_user.sshPublicKey:
        key_obj = user.ssh_keys.filter(active=False, system=system, ssh_public_key=key.decode('utf8').strip())
        if key_obj:
            ldap_user.sshPublicKey.delete(key)

    # Check if we have any keys stored in Bitu which should exist in LDAP. We compare the
    # keys stored in Bitu with the list from LDAP where the keys have been trimmed, to avoid
    # adding a key which already exist in LDAP, but with whitespace and a newline at the end.
    ldap_keys = [ldap_key.strip() for ldap_key in ldap_user.sshPublicKey]
    for key in user.ssh_keys.filter(system=system, active=True):
        if key.key_as_byte_string not in ldap_keys:
            ldap_user.sshPublicKey.add(key.key_as_byte_string)

    ldap_user.entry_commit_changes()
    load_ssh_key(user)


@job
def load_ssh_key(user: 'User'):
    """Import SSH keys from LDAP to Bitu database for a given user.

    Args:
        user (User): User
    """
    from keymanagement.models import SSHKey

    ldap_user = bituldap.get_user(user.get_username())

    # Load finger prints for keys in LDAP
    finger_prints = [SSHPublicKey(keydata=k.decode('utf8')).hash_sha512() for k in ldap_user.sshPublicKey]

    # Check if we have any keys that are listed as active, but not in LDAP.
    # LDAP is authoritive, so deactivate any keys not found.
    key: SSHKey
    for key in user.ssh_keys.filter(system=system):
        if key.active and key.get_finger_print() not in finger_prints:
            key.active = False
            key.save()

        if not key.active:
            key.system = ''
            key.save()

    # Map all our (Bitus) SSH keys to an dict, using finger prints
    # as keys.
    existing = {}
    for key in user.ssh_keys.all():
        existing[key.get_finger_print()] = key

    # Get all keys from LDAP and compare them to those in the database.
    for k in ldap_user.sshPublicKey.values:
        key_obj = SSHPublicKey(keydata=k.decode('utf8'))

        # Key already exists in the database and is correctly listed as active.
        # Skip futher processing.
        if key_obj.hash_sha512() in existing and existing[key_obj.hash_sha512()].active:
            continue

        # New key found in LDAP. Import and mark as active.
        if key_obj.hash_sha512() not in existing:
            ssh_key = SSHKey(
                user=user,
                ssh_public_key=k.decode('utf8'),
                system=system,
                comment=key_obj.comment,
                active=True)

            # Key does not have a comment, note in the database where we got the key
            # instead, to provide context for the user.
            if not ssh_key.comment:
                ssh_key.comment = f'Imported from {ssh_key.get_system_display()}'

            try:
                # Set _skip_signal to indicate that we do not want to trigger the
                # signals for syncronization with LDAP. Failure to do so will result
                # in multiple iteration, potentially endless.
                ssh_key._skip_signal = True
                ssh_key.save()
            except Exception as e:
                logger.warning(
                    f'failed to import ssh key from ldap for user: {user.get_username()}, exception was: {e}')

            # Add the new key and finger print to the list of existing keys, to avoid
            # processing identical keys from LDAP. LDAP doesn't validate the SSH keys
            # and it is possible to have a key listed multiple times.
            existing[ssh_key.get_finger_print()] = ssh_key

        # The key from LDAP does exist in Bitu, but is not active.
        # Update the key to indicate that it is currently used in LDAP
        elif not existing[key_obj.hash_sha512()].active:
            ssh_key = existing[key_obj.hash_sha512()]
            ssh_key.system = system
            ssh_key.active = True

            # Indicate that we do not want to process signals.
            ssh_key._skip_signal = True
            ssh_key.save()
