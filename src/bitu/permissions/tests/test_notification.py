from unittest import skip
from unittest.mock import patch

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
        self.rules = {
            'ldapbackend': {
                'cn=NDA,ou=groups,dc=example,dc=org': [{
                    'module': 'permissions.validators.manager_approval',
                    'managers': ['glopez', 'yharris'],
                    'count': 2
                }],
                'cn=staff,ou=groups,dc=example,dc=org': [{
                    'module': 'permissions.validators.manager_approval',
                    'managers': ['glopez', 'carol93'],
                    'notify': ['www@example.com', 'business@example.com'],
                    'count': 2
                }],
                'cn=db,ou=groups,dc=example,dc=org': [{
                    'module': 'permissions.validators.manager_approval',
                    'managers': ['yharris', 'carol93'],
                    'notify': ['admin@example.net', 'staff@example.org'],
                    'count': 2
                }, {
                    'module': 'permissions.validators.manager_approval',
                    'managers': ['yharris',],
                    'notify_group': ['cn=db-manager,ou=groups,dc=example,dc=org',],
                    'count': 1
                }],
            }
        }

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_group_notification(self, mock_connect):
        manager1 = User(username='glopez')
        manager2 = User(username='yharris')
        manager3 = User(username='carol93')
        manager1.save()
        manager2.save()
        manager3.save()

        with self.settings(ACCESS_REQUEST_RULES=self.rules):
            members = get_user_dns_from_ldap_group(['cn=db,ou=groups,dc=example,dc=org',])
            emails = get_notification_email_for_users(members)

            self.assertEqual(len(members), 4)
            self.assertEqual(len(emails), 4)

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_get_managers(self, mock_connect):
        # Load users which will act as our managers
        manager1 = User(username='glopez')
        manager2 = User(username='yharris')
        manager3 = User(username='carol93')
        manager1.save()
        manager2.save()
        manager3.save()

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
                key='cn=db,ou=groups,dc=example,dc=org',
                comment='Request'
            )

            self.assertEqual(len(mail.outbox), 7)
            self.assertEqual(mail.outbox[0].subject, 'Bitu IDM - Pending permission requests')

            PermissionRequest.objects.create(
                user=user,
                system='ldapbackend',
                key='cn=staff,ou=groups,dc=example,dc=org',
                comment='Request'
            )

            requests = get_pending_requests('glopez')
            self.assertEqual(len(requests), 1)
            self.assertEqual(len(mail.outbox), 9)  # 2 new email, plus the 7 previous

            requests = get_pending_requests('yharris')
            self.assertEqual(len(requests), 1)

            requests = get_pending_requests('carol93')
            self.assertEqual(len(requests), 2)

            request = PermissionRequest.objects.filter(key='cn=staff,ou=groups,dc=example,dc=org').first()
            managers = get_manager_emails(request)
            self.assertEqual(managers, {"www@example.com", "business@example.com"})
