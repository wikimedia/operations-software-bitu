# SPDX-License-Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING

from django.contrib.auth.tokens import PasswordResetTokenGenerator

if TYPE_CHECKING:
    from .models import Signup


class SignupActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, signup: "Signup", timestamp):
        """
        Hash the user's primary key, email, and some user state
        that's sure to change after activation to produce a token that is
        invalidated when it's used:
        1. The is_active field will change upon activation
        2. The last_update field will updated during activation.
        Failing those things, settings.PASSWORD_RESET_TIMEOUT eventually
        invalidates the token.
        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.
        """
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        last_update = (
            ""
            if signup.last_modified is None
            else signup.last_modified.replace(microsecond=0, tzinfo=None)
        )

        return f"{signup.pk}{signup.is_active}{last_update}{timestamp}{signup.email}"


default_token_generator = SignupActivationTokenGenerator()
