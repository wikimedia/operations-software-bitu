from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from signups.models import BlockListUsername, UserValidation


class UserValidationTests(APITestCase):
    def setUp(self):
        # Setup token authentication. Get user and add the correct permissions
        # to allow the user to access the API.
        self.user, _ = User.objects.get_or_create(username="robert25")
        content_type = ContentType.objects.get_for_model(UserValidation)
        permission = Permission.objects.get(
            codename="add_uservalidation",
            content_type=content_type,
        )
        self.user.user_permissions.add(permission)
        self.user.save()

        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_query(self):
        response = self.client.post('/signup/api/username/', {'username': 'generic user'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sanitized'], 'Generic user')
        self.assertEqual(response.data['uid'], 'genericuser')

        response = self.client.post('/signup/api/username/',
                                    {'username': 'generic user',
                                     'uid': 'generic'},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sanitized'], 'Generic user')
        self.assertEqual(response.data['uid'], 'generic')

    def test_blocklist(self):
        response = self.client.post('/signup/api/username/', {'username': 'pUpPet'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        BlockListUsername.objects.create(regex=r'(?i)puppet')
        response = self.client.post('/signup/api/username/', {'username': 'pUpPet'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ldap_validation(self):
        response = self.client.post('/signup/api/username/', {'username': self.user.username}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0], 'Invalid username, may already in use.')

    def test_url_validation(self):
        username = 'https://en.wikipedia.org'
        response = self.client.post('/signup/api/username/', {'username': username}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'][0], 'Invalid username, invalid format')


class BlockListIPTests(APITestCase):
    fixtures = ['signups/fixtures/blocklist_ip.json',]

    def setUp(self):
        # Setup token authentication. Get user and add the correct permissions
        # to allow the user to access the API.
        self.user, _ = User.objects.get_or_create(username="robert25")
        content_type = ContentType.objects.get_for_model(UserValidation)
        permission = Permission.objects.get(
            codename="add_uservalidation",
            content_type=content_type,
        )
        self.user.user_permissions.add(permission)
        self.user.save()

        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_block_single_ip(self):
        ip = '176.200.16.174'
        url = f'/signup/api/ip/{ip}/'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['network'], '176.200.16.174/32')

    def test_block_range(self):
        ip = '194.135.119.0'
        url = f'/signup/api/ip/{ip}/'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['network'], '194.135.119.0/24')

    def test_block_range_ipv6(self):
        ip = '2407:c800:2f22:6f8:::1001:0010'
        url = f'/signup/api/ip/{ip}/'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['network'], '2407:c800:2f22:6f8::/64')

    def test_block_expired(self):
        ip = '195.100.100.5'
        url = f'/signup/api/ip/{ip}/'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
