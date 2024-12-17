from unittest.mock import patch
from keymanagement.models import SSHKey

import bituldap

from django.contrib.auth import get_user_model
from django.test import TestCase

from ldapbackend import helpers, jobs

from . import dummy_ldap

User = get_user_model()


class LDAPSSHPublicKeyTest(TestCase):
    def setUp(self) -> None:
        # Hook up fakeredis
        # django_rq.queues.get_redis_connection = get_fake_connection

        self.test_key1 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE98KdrOV7JohIuejhoxwkhU4tXmyrscPCWDqeVAVXj3 Bitu test key 1"  # noqa: E501 line too long
        self.test_key2 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOxNideuQLvciH5ssbXrJAGUW4oPNVOcBJ/RlLQ5CEOI Bitu test key 2"  # noqa: E501 line too long

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_ldap_key_storage(self, mock_connect):
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

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_ssh_key_objects(self, mock_connect):
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
            self.assertEqual(key.key_type, 'ssh-ed25519')
            self.assertEqual(key.key_size, 256)

        ssh_key = SSHKey.objects.filter(user=user).first()
        self.assertTrue(ssh_key.active)
        self.assertEqual(ssh_key.system, 'ldapbackend')
        ssh_key.active = False
        ssh_key.save()

        ldap = bituldap.get_user(user)
        self.assertEqual(len(ldap.sshPublicKey), 1)
        self.assertNotIn(ssh_key.key_as_byte_string, ldap.sshPublicKey)

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_ldap_key_load(self, mock_connect):
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

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_force_unsync(self, mock_connect):
        key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID4iz39KixPqiHBYBEjU3ZkEI7DpaLnXBqFNSjGqLWmI Bitu Test Key"
        user, _ = User.objects.get_or_create(username='ahall')
        ldap = bituldap.get_user(user.get_username())

        self.assertIn(bytes(key, 'utf8'), ldap.sshPublicKey)

        key_obj = SSHKey(ssh_public_key=key, user=user, system='')
        key_obj.save()

        key_obj.refresh_from_db()
        self.assertTrue(key_obj.active)
        self.assertEqual(key_obj.comment, 'Bitu Test Key')
        self.assertEqual(key_obj.system, 'ldapbackend')

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_comment_cut_off(self, mock_connect):
        key1 = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBYfq+2dvlEWhIHOLL9BSXoxBm6mwU7mydyikBKDJPUM Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ridiculus mus mauris vitae ultricies leo integer malesuada. Mollis aliquam ut porttitor leo a diam sollicitudin tempor id. Integer enim neque volutpat ac tincidunt vitae. Eu nisl nunc mi ipsum faucibus vitae. Pretium aenean pharetra magna ac placerat. Pharetra vel turpis nunc eget lorem dolor sed viverra. Ac ut consequat semper viverra nam libero. Ut enim blandit volutpat maecenas volutpat blandit aliquam etiam erat. Aliquet enim tortor at auctor urna. Ultrices gravida dictum fusce ut placerat orci nulla."  # noqa: E501 line too long
        key2 = b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGmGHA9lWHG88gMJ+XYABoOve2zqPiOB+WiPwBakWXAh Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ridiculus mus mauris vitae ultricies leo integer malesuada. Mollis aliquam ut porttitor leo a diam sollicitudin tempor id. Integer e  \n "  # noqa: E501 line too long

        expected = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ridiculus mus mauris vitae ultricies leo integer malesuada. Mollis aliquam ut porttitor leo a diam sollicitudin tempor id. Integer e"  # noqa: E501 line too long

        comment1 = helpers.get_comment_from_imported_ssh_key(key1)
        comment2 = helpers.get_comment_from_imported_ssh_key(key2)
        self.assertEqual(len(comment1), 256)
        self.assertEqual(len(comment2), 256)
        self.assertEqual(comment1, expected)
        self.assertEqual(comment2, expected)

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_duplicate_keys(self, mock_connect):
        key1 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKB2+iW03Y5zAEQCw0+h0b9Y/1wcvFy7Vl+UbOwx8iaC LDAP duplication 1"
        key2 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKB2+iW03Y5zAEQCw0+h0b9Y/1wcvFy7Vl+UbOwx8iaC LDAP duplication 1\n"

        user, _ = User.objects.get_or_create(username='amy30')
        ldap = bituldap.get_user(user.get_username())
        ldap.sshPublicKey = [key1, key2]
        ldap.entry_commit_changes()

        ldap = bituldap.get_user(user.get_username())
        self.assertEqual(len(ldap.sshPublicKey), 2)

        jobs.load_ssh_key(user)
        self.assertEqual(len(user.ssh_keys.all()), 1)

        ssh_key = user.ssh_keys.first()
        self.assertEqual(ssh_key.system, 'ldapbackend')

        ssh_key.active = False
        ssh_key.save()

        ldap = bituldap.get_user(user.get_username())
        self.assertEqual(len(ldap.sshPublicKey), 0)

    @patch("bituldap.create_connection", return_value=dummy_ldap.connect())
    def test_key_cleanup(self, mock_connect):
        key1 = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC5slfyq3JcGv71K52pitHk+v5M7xSVgKT2zG7sgVcWvq+6aYzKxRE6HyPMSjW3NbVWre9673lz/hiTbqdGCf/l4IngQSjh3HHeZgILgpe1Jsgh2vGXEmEj/FBQSDmET4+m+xL5o+PZhXvhe55MQk1xq2tJM+UrfRrU5dhrhGLlh8Arl/8Ik3YWD7Q9PdmJB9vwWVvCBs10Vw55BYTDR4lSz3nkQa8UFjLhtruMpVBwmQ1e+sY8zR7Hd+C0H3Y6tL10RsSMuGiRJcMriQ8dOMa/tLMhMHbZ/+GAxaVlF0hJtsbWRN+xJ3clophZz7uD57MGa79lEQkiPzjl9Kfsjm4W1gFMaC/OovWIHZvGfIW4lx+o9KGG+SJAOVlCBPyk01xOmBHPDyNIebjepUsHk7MMDFFTSdqbkGcBgCRcjdyzLYW+s82E2ybs7c2wHH+uhcnxOn4GWHeWwPH+ZkHY1q4N3/1W+1hMLMooUPQLAZ4vzqzgtyGn9mN356bTzQ1yTyc=    \n"  # noqa: E501 line too long
        key2 = "           ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC5slfyq3JcGv71K52pitHk+v5M7xSVgKT2zG7sgVcWvq+6aYzKxRE6HyPMSjW3NbVWre9673lz/hiTbqdGCf/l4IngQSjh3HHeZgILgpe1Jsgh2vGXEmEj/FBQSDmET4+m+xL5o+PZhXvhe55MQk1xq2tJM+UrfRrU5dhrhGLlh8Arl/8Ik3YWD7Q9PdmJB9vwWVvCBs10Vw55BYTDR4lSz3nkQa8UFjLhtruMpVBwmQ1e+sY8zR7Hd+C0H3Y6tL10RsSMuGiRJcMriQ8dOMa/tLMhMHbZ/+GAxaVlF0hJtsbWRN+xJ3clophZz7uD57MGa79lEQkiPzjl9Kfsjm4W1gFMaC/OovWIHZvGfIW4lx+o9KGG+SJAOVlCBPyk01xOmBHPDyNIebjepUsHk7MMDFFTSdqbkGcBgCRcjdyzLYW+s82E2ybs7c2wHH+uhcnxOn4GWHeWwPH+ZkHY1q4N3/1W+1hMLMooUPQLAZ4vzqzgtyGn9mN356bTzQ1yTyc=    \n"  # noqa: E501 line too long

        user, _ = User.objects.get_or_create(username='amy30')
        self.assertEqual(user.ssh_keys.count(), 0)
        SSHKey.objects.create(user=user, ssh_public_key=key1, system='ldapbackend', active=True)
        self.assertEqual(user.ssh_keys.count(), 1)
        user.ssh_keys.first().delete()
        SSHKey.objects.create(user=user, ssh_public_key=key2, system='ldapbackend', active=True)
        self.assertEqual(user.ssh_keys.count(), 1)
        self.assertTrue(user.ssh_keys.first().ssh_public_key.startswith('ssh-rsa'))
