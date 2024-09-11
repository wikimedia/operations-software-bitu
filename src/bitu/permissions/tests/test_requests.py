from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from ldapbackend.tests import dummy_ldap
from permissions.models import PermissionRequest
from permissions.permission import permission_set


class PermissionRequestTest(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        # Required because we have the LDAPBackend installed and enabled.
        dummy_ldap.setup()
        dummy_ldap.create_test_users()

        # Get a user, who will be our requester.
        self.user, _ = User.objects.get_or_create(username='rachel32')
        self.user.set_password('secret')
        self.user.save()

        # Get our admin user, the owner of our LDAP group.
        self.admin, _ = User.objects.get_or_create(username='wwaller')
        self.admin.set_password('secret')
        self.admin.save()

    def test_permission_request(self):
        c = Client()
        c.login(username='rachel32', password='secret')

        list_url = reverse('permissions:list')
        request_url = reverse('permissions:request', kwargs={
            'system': 'ldapbackend',
            'key': 'cn=NDA,ou=groups,dc=example,dc=org'
        })

        pending_url = reverse('permissions:pending')

        response = c.get(list_url)
        self.assertContains(response, 'cn=NDA,ou=groups,dc=example,dc=org')
        self.assertNotContains(response, 'pending')

        response = c.post(request_url, {'comment': 'Please grant access'})
        self.assertEqual(response.status_code, 302)

        response = c.get(list_url)
        self.assertContains(response, 'Pending')

        c = Client()
        c.login(username='wwaller', password='secret')

        response = c.get(pending_url)
        self.assertContains(response, 'NDA (LDAP)', 1)

        permission_request = PermissionRequest.objects.get(user=self.user)
        approve_url = reverse('permissions:approve', kwargs={'pk': permission_request.pk})

        response = c.post(approve_url, {'comment': 'OK'})
        self.assertEqual(response.status_code, 302)

        response = c.get(pending_url)
        self.assertInHTML('<td>Approved</td>', str(response.content), 1)

    def test_filtering(self):
        """Test that users are not given their own requests to approve.
        """
        request = PermissionRequest.objects.create(
            user=self.admin,
            comment='Admin Test',
            key='cn=NDA,ou=groups,dc=example,dc=org',
            system='ldapbackend'
        )

        pending = permission_set.get_pending(self.admin).filter(pk=request.pk)
        self.assertEqual(0, pending.count())
