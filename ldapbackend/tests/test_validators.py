# SPDX-License-Identifier: GPL-3.0-or-later
from django.core.exceptions import ValidationError
from django.test import TestCase

from ldapbackend.validators import unix_username_regex_validator, login_shell_validator, unix_username_length_validator


class ValidatorTestCase(TestCase):
    def test_unix_username(self):
        self.assertRaises(ValidationError, unix_username_regex_validator, 'invalid#username')
        self.assertRaises(ValidationError, unix_username_regex_validator, 'invalid.username')

        # Do not delete, this is an actual test. If the validator fails an exception is
        # raised, counting as a failed test within the unit test framework. This check
        # must not raise an exception.
        unix_username_regex_validator('valid-test-username')

        self.assertRaises(ValidationError, unix_username_length_validator, 'abcdefghijklmnopvwxy12345678901234567890')
        unix_username_length_validator('abcdefghijklmnopvwxy1234567890-')


    def test_shell_validator(self):
        # Test with configuration
        with self.settings(BITU_SUB_SYSTEMS={'valid_shells': ['/bin/sh', '/bin/bash']}):
            self.assertRaises(ValidationError, login_shell_validator, '/bin/csh')
            login_shell_validator('/bin/sh')

        # Test without configuration
        self.assertRaises(ValidationError, login_shell_validator, '/bin/false')
        login_shell_validator('/bin/sh')