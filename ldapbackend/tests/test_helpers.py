import bituldap

from ldapbackend import helpers
from signups.models import Signup

from django.conf import settings
from django.test import TestCase
from unittest.mock import Mock

from . import dummy_ldap


class LDAPSignalTest(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        dummy_ldap.setup()

    def test_data_fill(self):
        signup:Signup = Signup(username='test', uid='test', email='TeSt@exaMple.com')
        signup.save()
        signup.set_password('password')

        user = bituldap.new_user(signup.uid)
        user = helpers.user_data_fill(signup, user)

        # Note that the attributes are not yet persisted to the LDAP server,
        # so we're accessing the "change" object values, hence the [0][1][0].
        self.assertEqual(user.loginShell.changes[0][1][0], '/bin/bash')
        self.assertEqual(user.mail.changes[0][1][0], signup.email.lower())
        self.assertEqual(user.gidNumber.changes[0][1][0], settings.LDAP_USER_CONF['default_gid'])
        self.assertEqual(user.sn.changes[0][1][0], user.cn.changes[0][1][0])
        self.assertEqual(user.sn.changes[0][1][0], 'Test')