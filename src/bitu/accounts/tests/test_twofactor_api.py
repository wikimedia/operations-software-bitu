import pyotp

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User, SecurityToken, Token
from ldapbackend.tests import dummy_ldap


class SecurityTokenAPITest(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        # Required because we have the LDAPBackend installed and enabled.
        dummy_ldap.setup()
        dummy_ldap.create_test_users()

        self.user, _ = User.objects.get_or_create(username='rachel32')
        self.user.set_password('secret')
        self.user.save()

        contenttype = ContentType.objects.get_for_model(SecurityToken)
        self.api_user, _ = User.objects.get_or_create(username='ethan07')
        self.api_user.set_password('secret')
        self.api_user.save()
        self.api_user.user_permissions.add(contenttype.permission_set.get(codename='add_securitytoken'))

    def test_2fa_api(self):
        totp_api = reverse('accounts:api_totp')

        # Create a security token for our test user.
        st = SecurityToken(user=self.user,)
        st.save()

        totp = pyotp.totp.TOTP(st.secret)

        # Create API token for API user.
        api_token = Token(user=self.api_user)
        api_token.save()

        # Authenticated API client
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + api_token.key)

        # User have no enabled security token, nor is the token valid.
        response = client.post(totp_api, {'user': self.user.get_username(), 'token': 123456})
        self.assertFalse(response.data['enabled'])
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['user'], self.user.get_username())

        # Enable 2FA token for user.
        st.enabled = True
        st.save()

        # Invalid token, 2FA is enabled, but token is wrong.
        # Avoid hardcoding token, because at some point 123456 will be a valid token.
        response = client.post(totp_api, {'user': self.user.get_username(), 'token': int(totp.now()) + 1})
        self.assertTrue(response.data['enabled'])
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['user'], self.user.get_username())

        token = totp.now()
        # Provide valid token.
        response = client.post(totp_api, {'user': self.user.get_username(), 'token': token})
        self.assertTrue(response.data['enabled'])
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['user'], self.user.get_username())

        # Provide valid, but "spent" token
        response = client.post(totp_api, {'user': self.user.get_username(), 'token': token})
        self.assertTrue(response.data['enabled'])
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['user'], self.user.get_username())

        # Check that a user with no SecurityToken is also not enabled.
        response = client.post(totp_api, {'user': self.api_user.get_username(), 'token': token})
        self.assertFalse(response.data['enabled'])
        self.assertFalse(response.data['valid'])
        self.assertEqual(response.data['user'], self.api_user.get_username())

        # Invalid credentials check
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + '1234567890abcdefghijklmnopqxyz')
        response = client.post(totp_api, {'user': self.user.get_username(), 'token': token})
        self.assertEqual(response.status_code, 401)
