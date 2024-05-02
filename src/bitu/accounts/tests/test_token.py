from django.test import TestCase
from django.test import Client
from django.urls import reverse

from accounts.models import User, Token
from ldapbackend.tests import dummy_ldap


class TokenUIAccessTest(TestCase):
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

    def test_keylisting(self):
        response = self.client.get(reverse('accounts:api_tokens'))
        self.assertContains(response, 'You do not current have any tokens.')

        response = self.client.post(reverse('accounts:api_token_create'), {'comment': 'TEST KEY'})
        token = Token.objects.filter(user=self.user).first()
        self.assertEqual(token.comment, 'TEST KEY')
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('accounts:api_tokens'))
        self.assertContains(response, token.comment)

        token = Token.objects.create(user=self.aux_user, comment='SECRET KEY')
        response = self.client.get(reverse('accounts:api_tokens'))
        self.assertNotContains(response, self.aux_user.get_username())
        self.assertNotContains(response, token.comment)

    def test_delete(self):
        token1 = Token.objects.create(user=self.user, comment=self.user.get_username)
        token2 = Token.objects.create(user=self.aux_user, comment=self.aux_user.get_username)
        self.assertEqual(Token.objects.count(), 2)

        response = self.client.delete(reverse('accounts:api_token_delete', kwargs={'pk': token2.pk}))
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(reverse('accounts:api_token_delete', kwargs={'pk': token1.pk}))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Token.objects.count(), 1)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 0)
