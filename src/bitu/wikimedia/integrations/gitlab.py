import logging

import requests

from django.conf import settings

logger = logging.getLogger('bitu')


class Gitlab():
    def __init__(self) -> None:
        self.base_url = settings.GITLAB['base_url']
        self.headers = {
            'PRIVATE-TOKEN': settings.GITLAB['token'],
            'Content-Type': 'application/json'
        }

    def lookup_user(self, cn: str) -> str:
        """Translate users LDAP username to Gitlab internal ID

        Use the GitLab API to find internal Gitlab ID for a given
        LDAP Common Name.

        Args:
            cn (str): User LDAP Common Name

        Raises:
            Exception: Lookup in Gerrit failed.

        Returns:
            str: Gitlab internal user ID
        """
        url = f'{self.base_url}/users?extern_uid={cn}&provider=openid_connect'
        resp = requests.get(url, headers=self.headers)

        if resp.status_code != 200:
            raise Exception(f'Failed to look up user in Gitlab, username: {cn}')

        data = resp.json()
        if len(data) > 1:
            logger.warning(f'Gitlab lookup returned multiple users, cn: {cn}')
            raise Exception(f'Gitlab lookup returned multiple users, cn: {cn}')
        elif len(data) == 0:
            logger.warning(f'Gitlab lookup found no user, cn: {cn}')
            raise Exception(f'Gitlab lookup found no user, cn: {cn}')
        logger.info(f'Gitlab, found user, cn: {cn}, gitlab_id: {data[0]["id"]}')
        return data[0]['id']

    def block_user(self, cn: str):
        """Block a user in Gitlab given an LDAP CN.

        Args:
            cn (str): LDAP Common Name

        Raises:
            Exception: Failed to locate user in Gitlab.
        """
        gitlab_id = self.lookup_user(cn)
        url = f'{self.base_url}/users/{gitlab_id}/block'
        resp = requests.post(url, headers=self.headers)

        if resp.status_code == 201:
            logger.info(f'Gitlab user blocked, cn: {cn}, gitlab_id: {gitlab_id}')
            return
        raise Exception(f'Gitlab, failed to block user, cn: {cn}, gitlab_id: {gitlab_id}')

    def unblock_user(self, cn: str):
        gitlab_id = self.lookup_user(cn)
        url = f'{self.base_url}/users/{gitlab_id}/unblock'
        resp = requests.post(url, headers=self.headers)

        if resp.status_code == 201:
            logger.info(f'Gitlab user unblocked, cn: {cn}, gitlab_id: {gitlab_id}')
            return
        raise Exception(f'Gitlab, failed to unblock user, cn: {cn}, gitlab_id: {gitlab_id}')
