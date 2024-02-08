from signups.models import Signup


from django.core import mail
from django.db.models.signals import post_save
from django.test import TestCase
from unittest.mock import Mock

from ldapbackend import jobs

from . import dummy_ldap


class LDAPSignalTest(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        dummy_ldap.setup()

    def test_signal_create(self):
        # Test that signal have been hooked up correctly.
        handlers = [s.__name__ for s in post_save._live_receivers(Signup) if s.__module__ == 'ldapbackend.signals']
        self.assertIn('create_user', handlers)

        # Hook up a new signal that we can check for execution.
        signal_handler = Mock(return_value=True)
        post_save.connect(signal_handler, Signup)

        signup: Signup = Signup(username='Test', uid='test', email='test@example.com')
        signup.set_password('password')
        self.assertFalse(signal_handler.called)

        self.assertEqual(signup.signuppassword_set.count(), 1)

        # Add a separate save, as the signaling will only trigger when
        # created is False and on first save this will be True
        signup.save()
        self.assertEqual(signal_handler.call_count, 1)

        signup.is_active = True
        signup.save()

        self.assertEqual(signal_handler.call_count, 2)

    def test_worker_function(self):
        signup: Signup = Signup(username='Test2', uid='test2', email='test2@example.com')
        signup.set_password('password')
        signup.is_active = True
        signup.save()

        with self.settings(ADMINS=['admin@example.com',]):
            self.assertTrue(jobs.create_user(signup))

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[BITU] LDAP user created: test2')
