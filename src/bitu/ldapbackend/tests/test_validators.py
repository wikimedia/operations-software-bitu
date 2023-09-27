# SPDX-License-Identifier: GPL-3.0-or-later
import bituldap

from django.core.exceptions import ValidationError
from django.test import TestCase

from ldapbackend.validators import unix_username_regex_validator, login_shell_validator, unix_username_length_validator, LDAPCommonNameValidator, LDAPUsernameValidator

from . import dummy_ldap


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


class LDAPValidatorTestCase(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        dummy_ldap.setup()
        dummy_ldap.create_test_users()

    def test_ldap_exists(self):
        self.assertRaises(ValidationError, LDAPCommonNameValidator, 'test1')
        self.assertRaises(ValidationError, LDAPUsernameValidator, 'test1')

        self.assertRaises(ValidationError, LDAPCommonNameValidator, 'Test1')
        self.assertRaises(ValidationError, LDAPUsernameValidator, 'Test1')

        LDAPCommonNameValidator('Test4')
        LDAPCommonNameValidator('test4')
        LDAPUsernameValidator('Test4')
        LDAPUsernameValidator('test4')


    def test_ldap_overlap(self):
        # Test that we catch combinations of CommonNames and UID where a UID is available,
        # but the CommonName isn't e.g.

        user = bituldap.new_user('test4')
        user.cn = 'Test5'
        user.sn = 'test5'
        user.uidNumber = 5000
        user.gidNumber = 5000
        user.homeDirectory = '/home/test5'
        user.entry_commit_changes()

        # We'd want to be able to use the multiple validators together and trigger a
        # validation error if either fails. This wrapper emulates adding multiple
        # validators to a given field.
        def wrap_multiple_validator(validators, username):
            for v in validators:
                v(username)

        self.assertRaises(ValidationError, LDAPUsernameValidator, 'test4')
        self.assertRaises(ValidationError, LDAPCommonNameValidator, 'test5')
        LDAPUsernameValidator('test5')
        LDAPCommonNameValidator('Test4')

        validators = [LDAPCommonNameValidator, LDAPUsernameValidator]
        self.assertRaises(ValidationError, wrap_multiple_validator, validators, 'test4')
        self.assertRaises(ValidationError, wrap_multiple_validator, validators, 'Test4')
        self.assertRaises(ValidationError, wrap_multiple_validator, validators, 'test5')
        self.assertRaises(ValidationError, wrap_multiple_validator, validators, 'Test5')

        wrap_multiple_validator(validators, 'test6')