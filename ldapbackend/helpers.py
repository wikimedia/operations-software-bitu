# SPDX-License-Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING

import bituldap
from django.conf import settings
from ldap3.utils.hashed import hashed
from ldap3 import HASHED_SALTED_SHA

if TYPE_CHECKING:
    from ldap3 import Entry

    from signups.models import Signup


def user_data_fill(signup: 'Signup', entry: 'Entry'):
    entry.sn = signup.username
    entry.uidNumber = bituldap.next_uid_number()
    entry.homeDirectory = f'/home/{signup.username.lower()}'
    entry.gidNumber = settings.LDAP_USER_CONF['default_gid']
    entry.userPassword = signup.signuppassword_set.get(module='ldapbackend').value
    return entry


default_ldap_user_data_fill = user_data_fill


def hash_password(password: str) -> str:
    hash_method = settings.BITU_SUB_SYSTEMS.get('ldapbackend', {}).get('password_hash_method', HASHED_SALTED_SHA)
    return hashed(hash_method, password)
