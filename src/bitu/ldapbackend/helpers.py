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

def capitalize_first(username: str) -> str:
    # Do not be tempted to replace this function with capitalize or title.
    # These methods do not do the same thing. Capitalize will ensure
    # that the the first letter is upper-case, and the remaining is
    # lower-case, mangling "John Doe" into "John doe". The reverse is the
    # true for "title", "john doe" will be returned as "John Doe" and while
    # that may be what the user intended, we cannot be sure, nor may it be
    # applicable in all languages.
    if not username:
        return username

    if len(username) == 1:
        return username.upper()

    return username[0].upper() + username[1:]


def user_data_fill(signup: 'Signup', entry: 'Entry'):
    # To ensure compatibility with MediaWiki, ensure that the first
    # character in cn and sn are capitalized, while touching none of
    # of the remaining characthers in the string.
    #
    # MediaWiki imposes the restriction that a username must always
    # start with a capital letter.
    entry.sn = capitalize_first(signup.username)
    entry.cn = capitalize_first(signup.username)

    entry.uid = signup.uid.lower()
    entry.uidNumber = bituldap.next_uid_number()
    entry.homeDirectory = f'/home/{signup.uid.lower()}'
    entry.gidNumber = settings.LDAP_USER_CONF['default_gid']
    entry.userPassword = signup.signuppassword_set.get(module='ldapbackend').value
    entry.mail = signup.email.lower()
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


def load_ssh_key(user):
    jobs.load_ssh_key.delay(user)

def syncronize_ssh_keys(user):
    jobs.syncronize_ssh_keys.delay(user)