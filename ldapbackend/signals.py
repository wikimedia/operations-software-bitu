# SPDX-License-Identifier: GPL-3.0-or-later
from . import jobs

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signups.models import Signup


def create_user(sender, instance: 'Signup', created: bool, **kwargs):
    if created:
        return

    if instance.is_active:
        jobs.create_user.delay(instance)
