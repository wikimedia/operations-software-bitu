import bituldap

from django.contrib.auth import get_user_model
from django.test import TestCase


from ldapbackend.tests import dummy_ldap
from permissions.models import PermissionRequest, Log as PermissionLog

User = get_user_model()


class PermissionRequestApprovalTest(TestCase):
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
                'nda': [{
                    'module': 'permissions.validators.manager_approval',
                    'managers': [self.manager1.get_username(), self.manager2.get_username()],
                    'count': 2
                }],
                'staff': [{
                    'module': 'permissions.validators.email_domain',
                    'domain': 'example.com',
                }],
                'www': [{
                    'module': 'permissions.validators.ldap_attribute',
                    'attribute': 'mail',
                    'operator': 'endswith',
                    'value': '@example.org'
                }, {
                    'module': 'permissions.validators.ldap_attribute',
                    'attribute': 'loginShell',
                    'operator': '__eq__',
                    'value': '/bin/ksh'
                }],
            }
        }

    def test_manager_approval(self):
        # Get a test users
        user = User(username='coxsarah')
        user.save()

        pr = PermissionRequest(user=user)
        pr.system = 'ldapbackend'
        pr.key = 'nda'
        pr.comment = 'Test access request'
        pr.save()

        with self.settings(ACCESS_REQUEST_RULES=self.rules):
            log = PermissionLog(request=pr, created_by=self.manager1, comment='Approved', approved=True)
            log.save()

            pr.refresh_from_db()
            self.assertFalse(pr.status == pr.APPROVED)

            # Check that one manager cannot just approve multiple times.
            log = PermissionLog(request=pr, created_by=self.manager1, comment='Approved', approved=True)
            log.save()

            pr.refresh_from_db()
            self.assertFalse(pr.status == pr.APPROVED)

            # Manager3 is not a manager for this permission/group, approval will do nothing.
            log = PermissionLog(request=pr, created_by=self.manager3, comment='Approved', approved=True)
            log.save()

            pr.refresh_from_db()
            self.assertFalse(pr.status == pr.APPROVED)

            log = PermissionLog(request=pr, created_by=self.manager2, comment='Approved', approved=True)
            log.save()

            pr.refresh_from_db()
            self.assertTrue(pr.status == pr.APPROVED)

    def test_email_domain_validation(self):
        # Get a test users
        user = User(username='coxsarah')
        user.save()

        pr = PermissionRequest(user=user)
        pr.system = 'ldapbackend'
        pr.key = 'staff'
        pr.comment = 'Test access request'
        pr.save()

        with self.settings(ACCESS_REQUEST_RULES=self.rules):
            pr.validate()
            pr.refresh_from_db

            self.assertFalse(pr.status == pr.APPROVED)
            entry = bituldap.get_user(uid=user.get_username())
            entry.mail = 'coxsarah@example.com'
            entry.entry_commit_changes()

            pr.validate()
            pr.refresh_from_db()
            self.assertTrue(pr.status == pr.APPROVED)

    def test_ldap_attributes_validation(self):
        # Get a test users
        user = User(username='coxsarah')
        user.save()

        pr = PermissionRequest(user=user)
        pr.system = 'ldapbackend'
        pr.key = 'www'
        pr.comment = 'Test access request'
        pr.save()

        with self.settings(ACCESS_REQUEST_RULES=self.rules):
            self.assertEqual(len(pr.rules), 2)
            pr.validate()
            pr.refresh_from_db

            self.assertFalse(pr.status == pr.APPROVED)

            entry = bituldap.get_user(uid=user.get_username())
            entry.mail = 'coxsarah@example.org'
            entry.loginShell = '/bin/ksh'
            entry.entry_commit_changes()

            pr.validate()
            pr.refresh_from_db

            self.assertTrue(pr.status == pr.APPROVED)
