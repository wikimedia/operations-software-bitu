# SPDX-License-Identifier: GPL-3.0-or-later
from urllib.parse import parse_qs, urlparse

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from social_django.models import UserSocialAuth

from accounts.models import User


OIDC_BACKEND = 'social_core.backends.open_id_connect.OpenIdConnectAuth'
MODEL_BACKEND = 'django.contrib.auth.backends.ModelBackend'


# base_settings does not install the social backends, but django.contrib.auth only
# resolves a session back to its user when the backend that created it is listed.
@override_settings(AUTHENTICATION_BACKENDS=[OIDC_BACKEND, MODEL_BACKEND],
                   SOCIAL_AUTH_OIDC_OIDC_ENDPOINT='https://idp.example.org/oidc')
class LogoutTest(TestCase):
    def setUp(self) -> None:
        self.user, _ = User.objects.get_or_create(username='rachel32')
        self.user.set_password('secret')
        self.user.save()

        self.client = Client()

    def associate(self, id_token='an-id-token'):
        return UserSocialAuth.objects.create(
            user=self.user,
            provider='oidc',
            uid=self.user.get_username(),
            extra_data={'id_token': id_token},
        )

    def test_oidc_session_is_ended_at_the_provider(self):
        self.associate()
        self.client.force_login(self.user, backend=OIDC_BACKEND)

        response = self.client.get(reverse('accounts:logout'))

        self.assertEqual(response.status_code, 302)
        location = urlparse(response.url)
        self.assertEqual(location.scheme, 'https')
        self.assertEqual(location.netloc, 'idp.example.org')
        self.assertEqual(location.path, '/oidc/logout')

        parameters = parse_qs(location.query)
        self.assertEqual(parameters['id_token_hint'], ['an-id-token'])
        self.assertEqual(parameters['post_logout_redirect_uri'],
                         ['http://testserver{}'.format(reverse('wikimedia:login'))])

    def test_post_logout_redirect_honours_the_next_parameter(self):
        self.associate()
        self.client.force_login(self.user, backend=OIDC_BACKEND)

        response = self.client.get('{}?next=/about/'.format(reverse('accounts:logout')))

        parameters = parse_qs(urlparse(response.url).query)
        self.assertEqual(parameters['post_logout_redirect_uri'], ['http://testserver/about/'])

    def test_post_logout_redirect_rejects_external_next_parameter(self):
        self.associate()
        self.client.force_login(self.user, backend=OIDC_BACKEND)

        response = self.client.get('{}?next=https://evil.example.net/'.format(reverse('accounts:logout')))

        parameters = parse_qs(urlparse(response.url).query)
        self.assertEqual(parameters['post_logout_redirect_uri'],
                         ['http://testserver{}'.format(reverse('accounts:logout'))])

    def test_local_session_does_not_reach_the_provider(self):
        self.client.login(username='rachel32', password='secret')

        response = self.client.get(reverse('accounts:logout'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('wikimedia:login'))

    def test_oidc_session_without_id_token_stays_local(self):
        self.associate(id_token=None)
        self.client.force_login(self.user, backend=OIDC_BACKEND)

        response = self.client.get(reverse('accounts:logout'))

        self.assertEqual(response.url, reverse('wikimedia:login'))

    @override_settings(SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=None,
                       SOCIAL_AUTH_OIDC_END_SESSION_URL=None)
    def test_unconfigured_provider_stays_local(self):
        self.associate()
        self.client.force_login(self.user, backend=OIDC_BACKEND)

        response = self.client.get(reverse('accounts:logout'))

        self.assertEqual(response.url, reverse('wikimedia:login'))

    @override_settings(SOCIAL_AUTH_OIDC_END_SESSION_URL='https://idp.example.org/oidc/endsession')
    def test_explicit_end_session_url_wins(self):
        self.associate()
        self.client.force_login(self.user, backend=OIDC_BACKEND)

        response = self.client.get(reverse('accounts:logout'))

        self.assertEqual(urlparse(response.url).path, '/oidc/endsession')

    def test_session_is_cleared(self):
        self.associate()
        self.client.force_login(self.user, backend=OIDC_BACKEND)

        self.client.get(reverse('accounts:logout'))

        response = self.client.get(reverse('accounts:overview'))
        self.assertEqual(response.status_code, 302)
