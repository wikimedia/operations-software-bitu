
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import re

import bituldap as b

from django.core import validators
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def LDAPUsernameValidator(username):
    try:
        user = b.get_user(username)
    except Exception as e:
        logger.warning(f"LDAP username validation error; username: {username}; {e}")
        raise ValidationError(
            _("Cannot validate username availability, please try again at later time"))

    if user:
        raise ValidationError(
            _("Invalid username, may already be used by subsystem"))


class UnixUsernameValidator(validators.RegexValidator):
    regex = r"^[a-z0-9]+\Z"
    message = _(
        "Enter a valid username. This value may contain only ASCII letters and "
        "numbers."
    )
    flags = re.ASCII


unix_username_validator = UnixUsernameValidator()


class LDAPPasswordValidator:
    def validate(self, password, user=None):
        pass
        # raise ValidationError("Your password did not match the requirements of the LDAP subsystem.")

    def get_help_text(self):
        return _(
            "Some rule for LDAP, if needed."
        )
