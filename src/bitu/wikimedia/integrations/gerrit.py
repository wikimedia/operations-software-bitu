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
        # By default Gerrit only matches active accounts (by automatically
        # adding `is:active`. Adding both ensure we get the account regardless
        # of its state.
        # https://phabricator.wikimedia.org/T307558#9625736
        url = f'{self.base_url}/r/a/accounts/?n=1&q=(is:inactive+OR+is:active)+username:{quote(uid)}'

        resp = requests.get(url, auth=self.auth, headers=self.headers)
        if resp.status_code != 200:
            logger.warning(f'Gerrit user lookup failed, username:{uid}, message: {resp.text}, http_code: {resp.status_code}')
            raise Exception('Gerrit user lookup failed')

        accounts = Gerrit.loadResponse(resp)

        # The API returns a list of AccountInfo entities and we limited it to 1 entry
        # https://gerrit.wikimedia.org/r/Documentation/rest-api-accounts.html#query-account
        if not accounts:
            logger.warning(f'Gerrit user not found, username:{uid}')
            raise Exception('Gerrit user not found')

        account = accounts.pop()

        if '_account_id' not in account:
            logger.error('Gerrit user lookup failed, no _account_id, username:{uid}')
            raise Exception('Gerrit user lookup failed')

        return account['_account_id']

    def update_user(self, uid, block):
        gerrit_account_id = self._lookup_user(uid)
        user = "%s (id: %s)" % (uid, gerrit_account_id)

        # The Gerrit API relies on PUT / DELETE to, respectively, activate or
        # deactivate an account.
        method = requests.delete if block else requests.put
        url = f'{self.base_url}/r/a/accounts/{gerrit_account_id}/active'

        # The response is solely reflected by the status code.
        resp = method(url, auth=self.auth)

        # DELETE to make an account inactive, the responses are:
        # - 204 account successfully made inactive (blocked)
        # - 409 account was already inactive (noop)
        #
        #
        # PUT to make an account active, the responses are:
        # - 200 account was already active (noop)
        # - 201 account becomes active (unblocked)
        #
        #
        # See also https://gerrit.wikimedia.org/r/c/operations/mediawiki-config/+/1011151

        resp_infos = f'http_status: {resp.status_code}, message: {resp.text}'
        status_code = resp.status_code

        # DELETE to make an account inactive
        # https://gerrit.wikimedia.org/r/Documentation/rest-api-accounts.html#delete-active
        if block:
            if status_code == 204:
                logger.info(f'{user} is now blocked in Gerrit')
            elif status_code == 409:
                logger.info(f'{user} is already blocked in Gerrit')
            else:
                logger.error(f'Failed to block user in Gerrit. {resp_infos}')
                raise Exception('Failed to block user in Gerrit.')

        # PUT to make an account active
        # https://gerrit.wikimedia.org/r/Documentation/rest-api-accounts.html#set-active
        else:
            if status_code == 200:
                logger.info(f'{user} was not blocked in Gerrit')
            elif status_code == 201:
                logger.info(f'{user} is now active in Gerrit')
            else:
                logger.error(f'Failed to unblock user in Gerrit. {resp_infos}')
                raise Exception('Failed to unblock user in Gerrit.')

    def block_user(self, uid):
        self.update_user(uid, block=True)

    def unblock_user(self, uid):
        self.update_user(uid, block=False)
