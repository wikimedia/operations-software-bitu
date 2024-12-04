from django.test import TestCase

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase


from ldapbackend.tests import dummy_ldap
from permissions.models import PermissionRequest
from permissions.notification import (get_manager_emails,
                                      get_pending_requests,
                                      get_permission_for_manager,
                                      get_user_dns_from_ldap_group,
                                      get_notification_email_for_users
                                      )


User = get_user_model()


class PermissionNotficationTests(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        dummy_ldap.setup()

        # Load users which will act as our managers
        self.manager1 = User(username='glopez')
        self.manager2 = User(username='yharris')
        self.manager3 = User(username='carol93')
        self.manager1.save()
        self.manager2.save()
        self.manager3.save()

        self.rules = {
            'ldapbackend': {
                'cn=NDA,ou=groups,dc=example,dc=org': [{
                    'module': 'permissions.validators.manager_approval',
                    'managers': [self.manager1.get_username(), self.manager2.get_username()],
                    'count': 2
                }],
                'cn=staff,ou=groups,dc=example,dc=org': [{
                    'module': 'permissions.validators.manager_approval',
                    'managers': [self.manager1.get_username(), self.manager3.get_username()],
                    'notify': ['www@example.com', 'business@example.com'],
                    'count': 2
                }],
                'cn=www,ou=groups,dc=example,dc=org': [{
                    'module': 'permissions.validators.manager_approval',
                    'managers': [self.manager2.get_username(), self.manager3.get_username()],
                    'notify': ['admin@example.net', 'staff@example.org'],
                    'count': 2
                }, {
                    'module': 'permissions.validators.manager_approval',
                    'managers': [self.manager2.get_username(),],
                    'notify_group': ['cn=staff,ou=groups,dc=example,dc=org',],
                    'count': 1
                }],
            }
        }

    def test_group_notification(self):
        with self.settings(ACCESS_REQUEST_RULES=self.rules):
            managers = get_user_dns_from_ldap_group(['cn=staff,ou=groups,dc=example,dc=org',])
            emails = get_notification_email_for_users(managers)

            # Our test data has some duplication, so we expect fewer email addresses than managers.
            self.assertEqual(len(managers), 868)
            self.assertEqual(len(emails), 865)

    def test_get_managers(self):
        user = User(username='coxsarah')
        user.save()

        with self.settings(ACCESS_REQUEST_RULES=self.rules):
            permissions = get_permission_for_manager('glopez')
            self.assertEqual(len(permissions), 2)

            permissions = get_permission_for_manager('yharris')
            self.assertEqual(len(permissions), 3)

            permissions = get_permission_for_manager('carol93')
            self.assertEqual(len(permissions), 2)

            PermissionRequest.objects.create(
                user=user,
                system='ldapbackend',
                key='cn=www,ou=groups,dc=example,dc=org',
                comment='Request'
            )

            self.assertEqual(len(mail.outbox), 867)
            self.assertEqual(mail.outbox[0].subject, 'Bitu IDM - Pending permission requests')

            PermissionRequest.objects.create(
                user=user,
                system='ldapbackend',
                key='cn=staff,ou=groups,dc=example,dc=org',
                comment='Request'
            )

            requests = get_pending_requests('glopez')
            self.assertEqual(len(requests), 1)
            self.assertEqual(len(mail.outbox), 869)  # Two new email, plus the 867 previous

            requests = get_pending_requests('yharris')
            self.assertEqual(len(requests), 1)

            requests = get_pending_requests('carol93')
            self.assertEqual(len(requests), 2)

            request = PermissionRequest.objects.filter(key='cn=staff,ou=groups,dc=example,dc=org').first()
            managers = get_manager_emails(request)
            self.assertEqual(managers, {"www@example.com", "business@example.com"})
