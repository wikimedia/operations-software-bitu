# SPDX-License-Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING

from django.contrib.auth.tokens import PasswordResetTokenGenerator

from .models import EmailUpdate

class BituUpdateEmailTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, data: EmailUpdate, timestamp):
        return f"{data.user.pk}{data.user.email}{data.user.last_login}{timestamp}{data.email}"

