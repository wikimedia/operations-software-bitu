from django.core import mail
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

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Bitu IDM - Pending permission requests')

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

    def test_reject_approve(self):
        # Create http client for requesting user permissions.
        c = Client()
        c.login(username='rachel32', password='secret')

        # Create http client for approving user permissions.
        c_admin = Client()
        c_admin.login(username='wwaller', password='secret')

        # Generic URLS:
        # * List user permission.
        # * List permissions pending approval.
        # * Request access to NDA group.
        list_url = reverse('permissions:list')
        pending_url = reverse('permissions:pending')
        request_url = reverse('permissions:request', kwargs={
            'system': 'ldapbackend',
            'key': 'cn=NDA,ou=groups,dc=example,dc=org'
        })

        # Check that user can request NDA group and has not done so already.
        response = c.get(list_url)
        self.assertContains(response, 'cn=NDA,ou=groups,dc=example,dc=org')
        self.assertNotContains(response, 'pending')

        # Request NDA group access and redirect to list.
        response = c.post(request_url, {'comment': 'Please grant access'})
        self.assertEqual(response.status_code, 302)

        # Check that list of permissions now include on pending request.
        response = c.get(list_url)
        self.assertContains(response, 'Pending')

        # Admin user should now have one permission for NDA to approve.
        response = c_admin.get(pending_url)
        self.assertContains(response, 'NDA (LDAP)', 1)

        # Reject request for NDA access, and check that the admin now sees
        # one rejection listed in the log entries.
        permission_request = PermissionRequest.objects.get(user=self.user)
        reject_url = reverse('permissions:reject', kwargs={'pk': permission_request.pk})
        response = c_admin.post(reject_url, {'comment': 'No'})
        self.assertEqual(response.status_code, 302)
        response = c_admin.get(pending_url)
        self.assertInHTML('<td>Rejected</td>', str(response.content), 1)

        # Reload permission request and verify that it has been rejected.
        permission_request.refresh_from_db()
        self.assertEqual(permission_request.status, PermissionRequest.REJECTED)

        # User retries request for access to the NDA group.
        response = c.post(request_url, {'comment': 'Please grant access'})
        self.assertEqual(response.status_code, 302)

        # Admin approves request
        permission_request = PermissionRequest.objects.get(user=self.user, status=PermissionRequest.PENDING)
        approve_url = reverse('permissions:approve', kwargs={'pk': permission_request.pk})
        response = c_admin.post(approve_url, {'comment': 'Yes'})
        self.assertEqual(response.status_code, 302)

        # Reload from database to check that status is now "Approved"
        permission_request.refresh_from_db()
        self.assertEqual(permission_request.status, PermissionRequest.APPROVED)

        # Admin log should include on rejection and one approval.
        response = c_admin.get(pending_url)
        self.assertInHTML('<td>Approved</td>', str(response.content), 1)
        self.assertInHTML('<td>Rejected</td>', str(response.content), 1)

        # Verify that the user now sees an approval.
        response = c.get(list_url)
        self.assertContains(response, 'NDA')
        self.assertContains(response, 'Approved')