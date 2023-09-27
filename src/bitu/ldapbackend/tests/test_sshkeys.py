from keymanagement.models import SSHKey

import bituldap
import django_rq

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.db.models.signals import post_save
from django.test import TestCase
from fakeredis import get_fake_connection
from unittest.mock import Mock

from keymanagement import signals
from ldapbackend import jobs

from . import dummy_ldap

User = get_user_model()

class LDAPSSHPublicKeyTest(TestCase):
    def setUp(self) -> None:
        # Setup a mock LDAP server.
        dummy_ldap.setup()

        # Hook up fakeredis
        # django_rq.queues.get_redis_connection = get_fake_connection

        self.test_key1 = "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBDsXepRu0Iv4+Z5Hw5gcLJ/n0cwKU//qypZ9Tgcsd7rSb+JWAZx2LenxN3FS998VL9k5Rz6Td4+P/ZH1TUvCS5Q= Bitu Test Key"
        self.test_key2 = "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBDqa1IgcSw6SDtgFdfnVDnhMbaacXnBaGxibqO/ga6c3Z3/dgFQVgHkFyqaPAg3XSHEK3uNPOa1unyiQT9WPRVw= Bitu Test Key"

    def test_ldap_key_storage(self):
        user = User(username='scott72')
        ldap = bituldap.get_user(user)

        self.assertEqual(user.get_username(), ldap.uid)

        key1 = b'My Secret SSH KEY'
        key2 = b'MySecret SSH KEY'
        ldap.sshPublicKey.add(key1)
        ldap.entry_commit_changes()

        ldap = bituldap.get_user(user)
        self.assertIn(key1, ldap.sshPublicKey)

        ldap.sshPublicKey.add(key2)
        ldap.entry_commit_changes()

        ldap = bituldap.get_user(user)
        self.assertIn(key1, ldap.sshPublicKey)
        self.assertIn(key2, ldap.sshPublicKey)
        self.assertEqual(len(ldap.sshPublicKey), 2)

    def test_ssh_key_objects(self):
        user = User(username='acarr')
        user.save()

        ssh_key = SSHKey()
        ssh_key.user = user
        ssh_key.system = 'ldapbackend'
        ssh_key.ssh_public_key = self.test_key1
        ssh_key.active = False
        ssh_key.save()

        ldap = bituldap.get_user(user)
        self.assertEqual(len(ldap.sshPublicKey), 0)

        ssh_key.active = True
        ssh_key.save()

        ldap = bituldap.get_user(user)
        self.assertEqual(len(ldap.sshPublicKey), 1)

        ssh_key = SSHKey()
        ssh_key.user = user
        ssh_key.system = 'ldapbackend'
        ssh_key.ssh_public_key = self.test_key2
        ssh_key.active = True
        ssh_key.save()

        ldap = bituldap.get_user(user)
        self.assertEqual(len(ldap.sshPublicKey), 2)
        self.assertTrue(ssh_key.active)

        # Delete all objects from the database and reload them from LDAP.
        SSHKey.objects.all().delete()
        self.assertFalse(SSHKey.objects.all())

        jobs.load_ssh_key(user)
        key_objects = SSHKey.objects.filter(user=user)
        ldap = bituldap.get_user(user)
        self.assertEqual(key_objects.count(), len(ldap.sshPublicKey))

        for key in key_objects:
            self.assertIn(key.key_as_byte_string, ldap.sshPublicKey)

        ssh_key = SSHKey.objects.filter(user=user).first()
        self.assertTrue(ssh_key.active)
        self.assertEqual(ssh_key.system, 'ldapbackend')
        ssh_key.active = False
        ssh_key.save()

        ldap = bituldap.get_user(user)
        self.assertEqual(len(ldap.sshPublicKey), 1)
        self.assertNotIn(ssh_key.key_as_byte_string, ldap.sshPublicKey)

    def test_ldap_key_load(self):
        user = User(username='tina93')
        user.save()

        ldap = bituldap.get_user(user.get_username())
        ldap.sshPublicKey.add(self.test_key1)
        ldap.entry_commit_changes()

        jobs.load_ssh_key(user)
        self.assertEqual(SSHKey.objects.filter(user=user).count(), 1)

        SSHKey.objects.filter(user=user).delete()
        self.assertFalse(SSHKey.objects.all())

        ssh_key = SSHKey()
        ssh_key.user = user
        ssh_key.ssh_public_key = self.test_key2
        ssh_key.active = True
        ssh_key.system = 'ldapbackend'
        ssh_key.save()

        ldap = bituldap.get_user(user.get_username())
        self.assertEqual(len(ldap.sshPublicKey), 2)
        self.assertEqual(SSHKey.objects.filter(user=user).count(), 2)