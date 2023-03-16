# SPDX-License-Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from ldap3 import Entry



class BituPasswordResetTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, entry: "Entry", timestamp):
        """
        Hash the user's username (uid), uidNumber, and some user state
        that's sure to change after activation to produce a token that is
        invalidated when it's used. The last_update field will change upon
        updating the password. Failing those things,
        settings.PASSWORD_RESET_TIMEOUT eventually invalidates the token.
        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.

        The hmac operation is handled by the super class, this function is
        only used to generate the input for _make_token_with_timestamp(),
        which in turn runs the output through salted_hmac(), provided by the
        django.utils.crypto module.
        """
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        last_update = (
            ""
            if getattr(entry, 'modifyTimestamp', None) is None
            else entry.modifyTimestamp.value.replace(microsecond=0, tzinfo=None)
        )

        return f"{entry.uid}{entry.uidNumber}{last_update}{timestamp}{entry.mail}"


default_token_generator = BituPasswordResetTokenGenerator()
