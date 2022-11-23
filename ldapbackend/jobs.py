# SPDX-License-Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING

import bituldap

from django.conf import settings
from django_rq import job
from . import helpers
if TYPE_CHECKING:
    from signups.models import Signup


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

create_user.delay()
