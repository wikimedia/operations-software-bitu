import pyotp
import time

from unittest.mock import patch

from django.test import TestCase
from django.test import Client
from django.urls import reverse

from accounts.models import User, SecurityToken
from ldapbackend.tests import dummy_ldap


class SecurityTokenTest(TestCase):
    def setUp(self) -> None:
        self.user, _ = User.objects.get_or_create(username='rachel32')
        self.user.set_password('secret')
        self.user.save()

        self.aux_user, _ = User.objects.get_or_create(username='ethan07')
        self.aux_user.set_password('secret')
        self.aux_user.save()

        self.client = Client()
        self.client.login(username='rachel32', password='secret')

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_basic_token_generation(self, mock_connect):
        st1, st1_create = SecurityToken.objects.get_or_create(user=self.user)
        st2, st2_create = SecurityToken.objects.get_or_create(user=self.aux_user)

        self.assertTrue(st1_create)
        self.assertTrue(st2_create)
        self.assertNotEqual(st1.secret, st2.secret)

        totp = pyotp.TOTP(st1.secret)
        token = totp.now()
        self.assertTrue(st1.validate(token))
        self.assertFalse(st2.validate(token))
        time.sleep(30)
        self.assertFalse(st1.validate(token))

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_token_enabled(self, mock_connect):
        enabled_url = reverse('accounts:2fa')

        # Ensure that the user does not have 2FA enabled or attempt to enabled
        # earlier.
        self.assertEqual(SecurityToken.objects.filter(user=self.user).count(), 0)

        # Trigger SecurityToken generation, so we can the secret
        response = self.client.get(enabled_url)
        self.user.refresh_from_db()
        secret = self.user.securitytoken.secret
        self.assertContains(
            response,
            f'<input type="hidden" name="security_token" value="{self.user.securitytoken.pk}" class="cdx-text-input__input" aria-describedby="cdx-security_token" id="id_security_token">',  # noqa
        )

        totp = pyotp.TOTP(secret)
        response = self.client.post(enabled_url,
                                    {'validation_code': totp.now(),
                                     'username': self.user.username,
                                     'security_token': self.user.securitytoken.pk})

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()

        # The form for enabling 2FA should generate 10 recovery keys
        self.assertEqual(self.user.securitytoken.recoverycode_set.count(), 10)
        self.assertTrue(self.user.securitytoken.enabled)

    def test_token_disable(self):
        disable_url = reverse('accounts:2fa_disable')

        self.assertEqual(SecurityToken.objects.filter(user=self.user).count(), 0)
        st = SecurityToken.objects.create(user=self.user, enabled=True)
        totp = pyotp.TOTP(st.secret)

        response = self.client.post(disable_url,
                                    {'validation_code': totp.now(),
                                     'username': self.user.username,
                                     'security_token': st.pk})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(0, SecurityToken.objects.filter(user=self.user).count())

    def test_recovery_code(self):
        # Test that we can disable 2FA using the recovery codes.
        disable_url = reverse('accounts:2fa_disable')
        st = SecurityToken.objects.create(user=self.user, enabled=True)
        st.create_recovery_codes()
        st.refresh_from_db()

        response = self.client.post(disable_url,
                                    {'validation_code': st.recoverycode_set.first().code,
                                     'username': self.user.username,
                                     'security_token': st.pk})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(0, SecurityToken.objects.filter(user=self.user).count())
