import bituldap

from ldapbackend import exceptions, helpers, jobs
from signups.models import Signup

from django.conf import settings
from django.test import TestCase
from unittest.mock import MagicMock, patch

from . import dummy_ldap

LDAP_UID_SETTINGS = [{'min': 100, 'max': 49999}, {'min': 1000000, 'max': 1999999}]
UID_START = 49997


def bituldap_new_uid():
    global UID_START
    UID_START = UID_START + 1
    return UID_START


class LDAPHelpersTest(TestCase):
    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_data_fill(self, mock_connect):
        signup: Signup = Signup(username='test', uid='test', email='TeSt@exaMple.com')
        signup.save()
        signup.set_password('password')

        user = bituldap.new_user(signup.uid)
        user = helpers.user_data_fill(signup, user)

        # Note that the attributes are not yet persisted to the LDAP server,
        # so we're accessing the "change" object values, hence the [0][1][0].
        self.assertEqual(user.loginShell.changes[0][1][0], '/bin/bash')
        self.assertEqual(user.mail.changes[0][1][0], signup.email.lower())
        self.assertEqual(user.gidNumber.changes[0][1][0], settings.LDAP_USER_CONF['default_gid'])
        self.assertEqual(user.cn.changes[0][1][0], 'Test')
        self.assertEqual(user.sn.changes[0][1][0], 'Test')

    def test_capitalize_username(self):
        self.assertEqual(helpers.capitalize_first(''), '')
        self.assertEqual(helpers.capitalize_first('a'), 'A')
        self.assertEqual(helpers.capitalize_first('A'), 'A')
        self.assertEqual(helpers.capitalize_first('Peter Jensen'), 'Peter Jensen')
        self.assertEqual(helpers.capitalize_first('Peter jensen'), 'Peter jensen')
        self.assertEqual(helpers.capitalize_first('peter jensen'), 'Peter jensen')
        self.assertEqual(helpers.capitalize_first('peter Jensen'), 'Peter Jensen')

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    @patch('bituldap.next_uid_number')
    def test_uid_validation(self, mock_next_uid_number: MagicMock, mock_connect: MagicMock):
        signup1: Signup = Signup(username='TestHelper1', uid='testhelper1', email='testhelper1@example.com')
        signup1.set_password('password')
        signup1.is_active = True
        signup1.save()

        signup2: Signup = Signup(username='TestHelper2', uid='testhelper2', email='testhelper2@example.com')
        signup2.set_password('password')
        signup2.is_active = True
        signup2.save()

        with self.settings(BITU_SUB_SYSTEMS={'ldapbackend': {'uid_ranges': LDAP_UID_SETTINGS}}):
            mock_next_uid_number.return_value = 49999
            self.assertEqual(helpers.get_new_uid(), 49999)
            self.assertTrue(jobs.create_user(signup1))

            mock_next_uid_number.return_value = 50000
            self.assertRaises(exceptions.UIDRangeException, helpers.get_new_uid)
            self.assertFalse(jobs.create_user(signup2))

            mock_next_uid_number.return_value = 1000000
            self.assertEqual(helpers.get_new_uid(), 1000000)
            self.assertTrue(jobs.create_user(signup2))
