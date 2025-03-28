import json
import logging

from  urllib.parse import quote

import requests

from django.conf import settings
from requests.auth import HTTPBasicAuth


logger = logging.getLogger('bitu')


class Gerrit():

    JSON_MAGIC = ')]}\''

    def __init__(self) -> None:
        self.auth = HTTPBasicAuth(settings.GERRIT['user'], settings.GERRIT['password'])
        self.base_url = settings.GERRIT['base_url']
        self.headers = {'User-Agent': settings.USER_AGENT,}

    @staticmethod
    def loadResponse(resp):
        if not resp.text.startswith(Gerrit.JSON_MAGIC):
            raise Exception('Json magic prefix could not be found in response')

        return json.loads(
            resp.text.removeprefix(Gerrit.JSON_MAGIC)
        )

    def _lookup_user(self, uid):
        url = f'{self.base_url}/r/a/accounts/?n=1&q=(is:inactive+OR+is:active)+username:{quote(uid)}'
        resp = requests.get(url, auth=self.auth, headers=self.headers)
        if resp.status_code != 200:
            logger.warning(f'Gerrit user lookup failed, username:{uid}, message: {resp.text}, http_code: {resp.status_code}')
            raise Exception('Gerrit user lookup failed')

        data = Gerrit.loadResponse(resp)

        if len(data) > 1:
            logger.error('Found multiple users in Gerrit, query: {uid}')
            raise Exception('Gerrit returned multiple users, single ID expected.')
        elif len(data) == 0:
            logger.warning(f'Gerrit user lookup failed, username:{uid}')
            raise Exception('Gerrit user not found')

        if '_account_id' in data[0]:
            return data[0]['_account_id']

        raise Exception('Gerrit user lookup failed')

    def update_user(self, uid, block):
        gerrit_id = self._lookup_user(uid)
        method = requests.delete if block else requests.put
        url = f'{self.base_url}/r/a/accounts/{gerrit_id}/active'
        resp = method(url, auth=self.auth)
        logger.info(f'Update user in Gerrit, username: {uid}, gerrit_id: {gerrit_id}, block: {block}, http_status: {resp.status_code}, message: {resp.text}')
        if resp.status_code not in [201, 204, 409]:
            logger.warning(f'Failed to update user in Gerrit, username: {uid}, gerrit_id: {gerrit_id}, status: {resp.status_code}, message: {resp.text}, block: {block}')
            raise Exception('Failed to updated user in Gerrit')

    def block_user(self, uid):
        self.update_user(uid, True)

    def unblock_user(self, uid):
        self.update_user(uid, False)