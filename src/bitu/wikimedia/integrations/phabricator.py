import json

from typing import Any

import requests

from django.conf import settings


class PhabClient:
    def __init__(self) -> None:
        if not settings.PHABRICATOR_API_TOKEN:
            raise RuntimeError('Phabricator API token not configured')
        
    def query(self, path: str, query: dict):
        query['__conduit__']= {'token': settings.PHABRICATOR_API_TOKEN}
        data = {'params': json.dumps(query),
                'outout': 'json'}
        url = f'{settings.PHABRICATOR_URI}/api/{path}'
        resp = requests.post(url, data=data)
        return resp.json()

    def lookup_user_by_cn(self, cn: str):
        resp = self.query('user.ldapquery', {
            'ldapnames': [cn,],
            'offset': 0,
            'limit': 1
        })

        print(resp)
        if not resp['result'] or len(resp['result']) < 0:
            raise Exception('Phabricator failed to lookup user.')
        elif len(resp['result']) > 1:
            raise Exception('Phabricator returned multiple users.')

        return resp['result'][0]

    def update_user_by_phid(self, PHID: str, disabled: bool):
        if not PHID.startswith('PHID-USER-'):
            raise Exception('Cannot block user, invalid Phabricator User ID.')

        path = 'user.edit'
        query = {
            'transactions': [{
                'type': 'disabled',
                'value': disabled
            },],
            'objectIdentifier': PHID
        }

        resp = self.query(path, query)
        return resp

    def block_user(self, cn:str):
        resp = self.lookup_user_by_cn(cn)
        phid = resp['phid']
        resp = self.update_user_by_phid(phid, True)
        if not resp['result']:
            raise Exception(resp['error_info'])
        return

    def unblock_user(self, cn:str):
        resp = self.lookup_user_by_cn(cn)
        phid = resp['phid']
        resp = self.update_user_by_phid(phid, False)
        if not resp['result']:
            raise Exception(resp['error_info'])
        return