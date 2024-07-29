import pyotp
import time

from django.test import TestCase
from django.test import Client
from django.urls import reverse

from accounts.models import User, SecurityToken
from ldapbackend.tests import dummy_ldap


class SecurityTokenTest(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        # Required because we have the LDAPBackend installed and enabled.
        dummy_ldap.setup()
        dummy_ldap.create_test_users()

        self.user, _ = User.objects.get_or_create(username='rachel32')
        self.user.set_password('secret')
        self.user.save()

        self.aux_user, _ = User.objects.get_or_create(username='ethan07')
        self.aux_user.set_password('secret')
        self.aux_user.save()

        self.client = Client()
        self.client.login(username='rachel32', password='secret')

    def test_basic_token_generation(self):
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

    def test_token_enabled(self):
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
        self.assertTrue(self.user.securitytoken.enabled)

    def test_token_disable(self):
        enabled_url = reverse('accounts:2fa_disable')

        self.assertEqual(SecurityToken.objects.filter(user=self.user).count(), 0)
        st = SecurityToken.objects.create(user=self.user, enabled=True)
        totp = pyotp.TOTP(st.secret)

        response = self.client.post(enabled_url,
                                    {'validation_code': totp.now(),
                                     'username': self.user.username,
                                     'security_token': st.pk})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(0, SecurityToken.objects.filter(user=self.user).count())
