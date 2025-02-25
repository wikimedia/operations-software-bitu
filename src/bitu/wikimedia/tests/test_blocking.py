from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


from ldapbackend.tests import dummy_ldap

User = get_user_model()


class BlockSearch(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        dummy_ldap.setup()

        self.user, _ = User.objects.get_or_create(username='acarr')
        self.user.set_password('secret')
        self.user.save()

    def test_search(self):
        c = Client()
        c.login(username='acarr', password='secret')

        url = reverse('wikimedia:block_search')

        with self.settings(BITU_LDAP={'users': {'dn': 'ou=people,dc=example,dc=org'}}, ACCOUNT_MANAGERS=['acarr',]):
            response = c.post(url, {'username': 'billy'})
            self.assertContains(response, '<td>billy09</td>')

            response = c.post(url, {'username': 'gregoryvasquez@example.net'})
            self.assertContains(response, '<td>billy09</td>', count=2)
