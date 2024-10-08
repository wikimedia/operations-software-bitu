
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import re

import bituldap as b

from django.conf import settings
from django.core import validators
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from passlib.hash import ldap_salted_sha1 as lsm

logger = logging.getLogger(__name__)


def LDAPUsernameValidator(username: str):
    """LDAP username validator.

    Check that the provided username is not used as a UID by the LDAP backend.

    Args:
        username (str): Desired username

    Raises:
        ValidationError: Raise if the username cannot be used.
    """

    try:
        user = b.get_user(username)
    except Exception as e:
        logger.warning(f"LDAP username validation error; username: {username}; {e}")
        raise ValidationError(
            _("Cannot validate username availability, please try again at later time"))

    if user:
        raise ValidationError(
            _("Invalid username, may already in use."))


def LDAPCommonNameValidator(username: str):
    """LDAP username validator.

    Check that the provided username is not used as a CommonName by the LDAP backend.

    Args:
        username (str): Desired username

    Raises:
        ValidationError: Raise if the username cannot be used.
    """

    try:
        user = b.get_single_object(b.read_configuration().users, 'cn', username)
    except Exception as e:
        logger.warning(f"LDAP CommonName validation error; username: {username}; {e}")
        raise ValidationError(
            _("Cannot validate username availability, please try again at later time"))

    if user:
        raise ValidationError(
            _("Invalid username, may already in use."))


def LDAPEmailValidator(email: str):
    """LDAP email validator.

    Check that the provided email is not already in use by
    another LDAP user.

    Args:
        email (str): Email address to check

    Raises:
        ValidationError: Raised when email address cannot be used.
    """

    try:
        user = b.get_single_object(b.read_configuration().users, 'mail', email)
    except Exception as e:
        # TODO: Bitu-LDAP needs to be expanded with a specialised exception.
        # The exception could be a communication error, or a result of multiple
        # user objects with the same email address. This should be two separate
        # errors.
        logger.warning("LDAP email validation error; email %s; %s", email, e)
        raise ValidationError(
            _("Invalid email, already in use."))

    if user:
            raise ValidationError(_("Invalid email, already in use."))


class UnixUsernameRegExValidator(validators.RegexValidator):
    regex = r"^[a-z0-9\-]+\Z"
    message = _(
        "Enter a valid username. This value may contain only ASCII letters, "
        "numbers and -"
    )
    flags = re.ASCII


unix_username_regex_validator = UnixUsernameRegExValidator()


def unix_username_length_validator(username: str):
    if len(username) > 32:
        raise ValidationError(
            _("SSH access (shell) usernames can be no more than 32 characters in length"))


class LDAPPasswordValidator:
    """Validator for LDAP password policy
    """
    def validate(self, password, user=None):
        pass
        # raise ValidationError("Your password did not match the requirements of the LDAP subsystem.")

    def get_help_text(self):
        return _(
            "Some rule for LDAP, if needed."
        )


def ldap_password_verification(username: str, password: str):
    ldap_user = b.get_user(username)
    if not lsm.verify(password, ldap_user.userPassword.value):
        raise ValidationError(
            _("Invalid password"), code='invalid_ldap_password')


def login_shell_validator(shell: str):
    shells = ['/bin/sh',
              '/bin/bash',
              '/usr/bin/bash',
              '/bin/rbash',
              '/usr/bin/rbash',
              '/bin/dash',
              '/bin/ksh',
              '/usr/bin/dash',
              '/usr/bin/tmux',
              '/usr/bin/screen',
              '/bin/zsh',
              '/usr/bin/zsh',]

    if shell not in settings.BITU_SUB_SYSTEMS.get('valid_shells', shells):
        raise ValidationError(
            _("Does not appear to be a valid shell path."))