import json
from unittest.mock import patch, Mock, ANY

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

import bituldap

from ldapbackend.tests import dummy_ldap

User = get_user_model()


class TestIntegrations(TestCase):

    @classmethod
    def setUpTestData(cls):
        dummy_ldap.setup()

        admin, _ = User.objects.get_or_create(username='admin')
        admin.set_password('secret')
        admin.save()

        user = bituldap.new_user(uid='jdoe')
        user.cn = 'Jane Doe'
        user.mail = 'jane.doe@example.org'
        # Mandatories:
        user.sn = 'some sn'
        user.uidNumber = 1911
        user.gidNumber = 777
        user.homeDirectory = '/home/jdoe'
        user.entry_commit_changes()

        cls.user_entry = user

    def setUp(self):
        self.as_admin = Client()
        self.as_admin.login(username='admin', password='secret')

    def do(self, action, client_name):
        block_action_url = reverse(
            'wikimedia:%s' % action,
            kwargs={'username': 'jdoe'},
        )

        with (
            self.settings(
                ACCOUNT_MANAGERS=['admin'],
                USER_AGENT='Bitu User Agent (test)',
                GERRIT={
                    'user': 'gerritbituuser',
                    'password': 'secret',
                    'base_url': 'https://review.example.org/r',
                },
                GITLAB={
                    'base_url': 'https://gitlab.example.org',
                    'token': '42',
                },
                PHABRICATOR_API_TOKEN='99',
                PHABRICATOR_URI='https://phab.example.org',
            ),
            self.assertLogs('bitu', level='INFO') as logs,
        ):
            response = self.as_admin.post(block_action_url, {
                'action': action,
                'comment': 'doing action: %s' % action,
                'created_by': 'admin',
                'username': 'jdoe',
            })
            self.assertRedirects(
                response,
                expected_url='/wikimedia/block/?q=jdoe',
                fetch_redirect_response=False,
            )
        return logs

    @override_settings(_UPDATE_ACCOUNT_CLIENTS_NAMES='ldap')
    @override_settings(BITU_LDAP={
        'users': {'dn': 'ou=people,dc=example,dc=org'},
        'ppolicy': 'cn=disabled,ou=ppolicies,dc=example,dc=org',
    })
    def test_ldap__update_user(self):
        # LDAP client
        mock_ldap_connection = Mock()
        mock_ldap_connection.search.return_value = ['some response']
        mock_ldap_connection.response = [TestIntegrations.user_entry]
        mock_ldap_connection.modify.return_value = True
        patch('bituldap.create_connection', return_value=(True, mock_ldap_connection))
        patch('bituldap.get_user', return_value=TestIntegrations.user_entry)

        with self.subTest(action='block_user'):
            logs = self.do('block_user', 'ldap')
            expected = 'INFO:bitu:ldap, account blocked, username: jdoe, locktime: '
            assert logs.output[0].startswith(expected), \
                'Could not find expected %s in %s' % (expected, logs.output)

        with self.subTest(action='unblock_user'):
            self.skipTest('Not implemented')

    @override_settings(_UPDATE_ACCOUNT_CLIENTS_NAMES='gerrit')
    @patch('wikimedia.integrations.gerrit.requests')
    def test_gerrit__update_user(self, requests):
        requests.get.return_value = Mock(
            status_code=200,
            text=')]}\'' + json.dumps([{'_account_id': 7777}]),
        )

        cases = {
            'blocking': {
                'update_api': requests.delete,
                'returns': 204,
                'action': 'block_user',
                'expected_log': 'INFO:bitu:jdoe (id: 7777) is now blocked in Gerrit',
            },
            'already blocked': {
                'update_api': requests.delete,
                'returns': 409,
                'action': 'block_user',
                'expected_log': 'INFO:bitu:jdoe (id: 7777) is already blocked in Gerrit',
            },
            'blocking action fails': {
                'update_api': requests.delete,
                'returns': 503,
                'action': 'block_user',
                'expected_log': 'ERROR:bitu:Failed to block user in Gerrit. http_status: 503, message: ',
            },

            'unblock': {
                'update_api': requests.put,
                'returns': 200,
                'action': 'unblock_user',
                'expected_log': 'INFO:bitu:jdoe (id: 7777) was not blocked in Gerrit',
            },
            'already unblocked': {
                'update_api': requests.put,
                'returns': 201,
                'action': 'unblock_user',
                'expected_log': 'INFO:bitu:jdoe (id: 7777) is now active in Gerrit',
            },
            'unblocking action fails': {
                'update_api': requests.put,
                'returns': 503,
                'action': 'unblock_user',
                'expected_log': 'ERROR:bitu:Failed to unblock user in Gerrit. http_status: 503, message: ',
            },
        }

        for title, p in cases.items():
            with self.subTest(title=title):
                # Configure the request
                p['update_api'].return_value = Mock(status_code=p['returns'], text='')

                logs = self.do(p['action'], 'gerrit')

                # Assertions
                p['update_api'].assert_called_with('https://review.example.org/r/r/a/accounts/7777/active', auth=ANY)
                self.assertIn(p['expected_log'], logs.output)

    @override_settings(_UPDATE_ACCOUNT_CLIENTS_NAMES='gitlab')
    @patch('wikimedia.integrations.gitlab.requests')
    def test_gitlab__update_user(self, requests):
        self.skipTest('Not implement yet')

    @override_settings(_UPDATE_ACCOUNT_CLIENTS_NAMES='phabricator')
    @patch('wikimedia.integrations.phabricator.requests')
    def test_phabricator__update_user(self, requests):
        self.skipTest('Not implement yet')
