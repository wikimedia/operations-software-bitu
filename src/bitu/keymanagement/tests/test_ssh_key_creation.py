from django.test import TestCase
from django.test import Client
from django.urls import reverse

from accounts.models import User
from keymanagement.models import SSHKey

from ldapbackend.tests import dummy_ldap


class ValidatorTest(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        # Required because we have the LDAPBackend installed and enabled.
        dummy_ldap.setup()
        dummy_ldap.create_test_users()

        self.user, _ = User.objects.get_or_create(username='rachel32')
        self.user.set_password('secret')
        self.user.save()

        self.client = Client()
        self.client.login(username='rachel32', password='secret')

    def test_create_insecure(self):
        """Test that only explicitly allowed key types are accepted.
        """
        dsa_key = 'ssh-dss AAAAB3NzaC1kc3MAAACBAJWKnNZ0FKMM1AOx78yPumR2YDGVrWN1IsEq+9oRHwofhmfLdVkRLXGmemapbXnSzFEqMsJiXziMqzxOBvvX+e/QE2FOvr3vUZgunHDcdi9lCb+7kPY6Vmc4k8nDyKwTWGlPm6dif3OQmtQXZcGGmm0uN6evfIGrt6c1czUvcCINAAAAFQDNYQ3Zea/1HVoZfTP0ZKC7qZZsTQAAAIEAhLjEpoHHus53XJ/O0cc9OCnNmOS4szU5sOefmBb3T0QOxtd8rloC72PIW+ErPgaKZFqjwHYmQhuwrSPl9yZARW+keYYizNUGFt6SWNaqBuqJzMTK9n8LmXQZiRE8B5YvdglHRNvs+XQpVAilk3pLXq2C5+wfTN7j/z40qRUvUGMAAACARNx1niuooHytbCY4ci5hOxUiuEokG7I4/WJyRyN403gnE+oYpKXEk4oYG45lSlCHofhlNyV4LMxg2ozhYu6I0Zc3ffzItlC702X81xCPWtfBEcyXvCL/6+1xYpn65X4nxLtrIAIFpH6h2SVHyBzJViMiwxJmqmXl7ztwH6PFV1w= Bitu DSA Test Key'  # noqa
        create_url = reverse('keymanagement:create')

        allowed_keys = {'allowed_key_type': {'ssh-rsa': {}, 'ssh-ecdsa': {}, 'ssh-ed25519': {}}}

        with self.settings(BITU_SSH_KEY_VALIDATOR=allowed_keys):
            response = self.client.post(create_url, {'comment': 'Insecure DSA', 'ssh_public_key': dsa_key})
            keys = SSHKey.objects.filter(user=self.user).all()
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Key type ssh-dss')
            self.assertEqual(0, keys.count())

    def test_create_view_dublication(self):
        """Test that the create view will trigger and respond correctly to in use validator.
        """
        key1 = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINTXBZrJkodCzdfHkuKy2+/yPHLrMkkMYWfIuDGaJy8t Bitu ED25519 Test Key 1'  # noqa
        key2 = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINTXBZrJkodCzdfHkuKy2+/yPHLrMkkMYWfIuDGaJy8t Bitu ED25519 Test Key 2'  # noqa

        create_url = reverse('keymanagement:create')
        list_url = reverse('keymanagement:list')
        response = self.client.post(create_url, {'comment': 'Test ed25519 key', 'ssh_public_key': key1})
        self.assertEqual(response.status_code, 302)

        keys = SSHKey.objects.filter(user=self.user).all()
        self.assertEqual(1, keys.count())

        response = self.client.post(create_url, {'comment': 'Test ed25519 key 2', 'ssh_public_key': key2})
        keys = SSHKey.objects.filter(user=self.user).all()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SSH key already exists')
        self.assertEqual(1, keys.count())

        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, key1)
        self.assertEqual(keys[0], self.user.ssh_keys.all()[0])
