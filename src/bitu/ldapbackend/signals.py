# SPDX-License-Identifier: GPL-3.0-or-later
from . import jobs

from typing import TYPE_CHECKING


from django.contrib.auth import get_user_model


if TYPE_CHECKING:
    from signups.models import Signup
    User = get_user_model()


def create_user(sender, instance: 'Signup', created: bool, **kwargs):
    if created:
        return

    if instance.is_active:
        jobs.create_user.delay(instance)


def update_user(sender, instance: 'User', created: bool, **kawrgs):
    jobs.update_ldap_attributes.delay(instance, {'mail': instance.email})