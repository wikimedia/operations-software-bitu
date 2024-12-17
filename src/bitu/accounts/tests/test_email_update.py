import re

from unittest.mock import patch

import bituldap

from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from ldapbackend.tests import dummy_ldap


class TestEmailModelUpdate(TestCase):
    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_unsynced(self, mock_connect):
        user, _ = User.objects.get_or_create(username='amiller', email='smithjohn@example.org')
        user.set_password('secret')
        user.save()
        email = user.email
        ldap_user = bituldap.get_user(user.get_username())

        self.assertEqual(str(ldap_user.mail), user.email)
        user.email = 'amiller@example.org'
        user.save()

        self.assertNotEqual(user.email, email)

        ldap_user = bituldap.get_user(user.get_username())
        self.assertNotEqual(str(ldap_user.mail), user.email)


class TestEmailUpdateFlow(TestCase):
    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_email_update_flow(self, mock_connect):
        self.user, _ = User.objects.get_or_create(username='amiller', email='smithjohn@example.org')
        self.user.set_password('secret')
        self.user.save()

        new_email = 'amiller@example.org'
        url = reverse('accounts:email')
        user = User.objects.get(username='amiller')
        client = Client()
        client.login(username='amiller', password='secret')

        response = client.post(url, {'email1': new_email, 'email2': new_email})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

        # Extract verification URL from email
        body = mail.outbox[0].body
        m = re.search('https:\/\/(.*)\/', body)
        verify_url = m.group(0).removeprefix('https://localhost')

        response = client.post(verify_url)
        redirect_url = response.headers['Location']

        # Providing the parameters are only required due to how the testing framework operated.
        # Under normal conditions user_id and email is automatically inserted.
        response = client.post(redirect_url, {'user_id': user.id, 'email': 'not_valid@example.com'})

        # If the email provided in the form differs from the email originally provide, we should get
        # an error.
        self.assertEqual(response.status_code, 403)

        # Call update page with correct parameters.
        response = client.post(redirect_url, {'user_id': user.id, 'email': new_email})
        self.assertEqual(response.status_code, 302)

        ldap_user = bituldap.get_user('amiller')
        self.assertEqual(str(ldap_user.mail), new_email)


