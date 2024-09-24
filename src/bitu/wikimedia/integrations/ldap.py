import logging

import bituldap

from django.conf import settings
from django.utils import timezone
from ldap3 import SUBTREE, MODIFY_REPLACE, MODIFY_DELETE


logger = logging.getLogger('bitu')


class LDAP():
    def fetch_entry(self, uid) -> dict:
        success, conn = bituldap.create_connection()
        conn.search(
            search_base=settings.BITU_LDAP['users']['dn'],
            search_filter=f'(uid={uid})',
            search_scope=SUBTREE,
            attributes=['uid', 'pwdAccountLockedTime', 'pwdPolicySubEntry'])

        if not success or len(conn.response) != 1:
            raise Exception(f'ldap blocking, failed to lookup user, username: {uid}\
, success: {success}, results: {len(conn.response)}')
        return conn.response[0]

    def block_user(self, uid):
        entry = self.fetch_entry(uid)
        timestamp = timezone.now().strftime('%Y%m%d%H%MZ')
        success, conn = bituldap.create_connection()
        success = conn.modify(entry['dn'], {
            'pwdPolicySubEntry': [(MODIFY_REPLACE, [settings.BITU_LDAP['ppolicy']])],
            'pwdAccountLockedTime': [(MODIFY_REPLACE, [timestamp])],
        })

        if not success:
            logger.error(f'ldap, account blocked failed, username: {uid}, locktime: {timestamp}')
            raise Exception(f'ldap, failed to block user, username: {uid}')
        logger.info(f'ldap, account blocked, username: {uid}, locktime: {timestamp}')

    def unblock_user(self, uid):
        entry = self.fetch_entry(uid)
        success, conn = bituldap.create_connection()
        success = conn.modify(entry['dn'], {
            'pwdAccountLockedTime': [(MODIFY_DELETE, [entry['attributes']['pwdAccountLockedTime']])],
        })

        if not success:
            logger.error(f'ldap, account unblocked failed, username: {uid}')
            raise Exception(f'ldap, failed to unblock user, username: {uid}')
        logger.info(f'ldap, account unblocked, username: {uid}')
