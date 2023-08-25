# SPDX-License-Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING

import bituldap

from . import jobs
from django.conf import settings
from ldap3.utils.hashed import hashed
from ldap3 import HASHED_SALTED_SHA


if TYPE_CHECKING:
    from ldap3 import Entry
    from signups.models import Signup
    from keymanagement.models import SSHKey

def user_data_fill(signup: 'Signup', entry: 'Entry'):
    entry.sn = signup.username.capitalize()
    entry.cn = signup.username.capitalize()
    entry.uid = signup.uid.lower()
    entry.uidNumber = bituldap.next_uid_number()
    entry.homeDirectory = f'/home/{signup.uid.lower()}'
    entry.gidNumber = settings.LDAP_USER_CONF['default_gid']
    entry.userPassword = signup.signuppassword_set.get(module='ldapbackend').value
    entry.mail = signup.email
    entry.loginShell = '/bin/bash'
    return entry


default_ldap_user_data_fill = user_data_fill


def hash_password(password: str) -> str:
    """Provide as hash appropriate for the LDAP backend

    The hashing function can be configured in the Django
    settings file. The default hashing method is SSHA1,
    see: https://www.openldap.org/faq/data/cache/347.html

    .. code-block:: python

       BITU_SUB_SYSTEMS: {
         'ldapbackend': {
            'password_hash_method': HASHED_SALTED_SHA
         }
       }

    Args:
        password: plaintext password

    Returns:
        str: password hash
    """
    hash_method = settings.BITU_SUB_SYSTEMS.get('ldapbackend', {}).get('password_hash_method', HASHED_SALTED_SHA)
    return hashed(hash_method, password)


def check_ssh_key(key: 'SSHKey'):
    jobs.check_ssh_key.delay(key)


def update_ssh_key(key: 'SSHKey'):
    jobs.update_ssh_key.delay(key)


def remove_ssh_key(key: 'SSHKey'):
    jobs.remove_ssh_key.delay(key)


def load_ssh_key(key: 'SSHKey'):
    jobs.load_ssh_key.delay(key)

