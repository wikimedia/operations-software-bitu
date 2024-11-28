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
            attributes=['cn', 'uid', 'mail', 'pwdAccountLockedTime', 'pwdPolicySubEntry'])

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

    def unblock_user(self, uid: str):
        """Unblock an LDAP account.

        Args:
            uid (str): uid, Unix username.

        Raises:
            Exception: Failed to delete LDAP attribute.
        """

        # Fetch user entry, use internal fetch_entry to get policy attributes included.
        entry = self.fetch_entry(uid)

        # Create new LDAP connection, as modifying policy attributes requires raw LDAP queries
        # and cannot be done using the LDAP3 abstraction layer.
        success, conn = bituldap.create_connection()
        if not success:
            logger.error(f'ldap, account unblocked failed, could not create connection, username: {uid}')
            raise Exception(f'ldap, failed to unblock user, username: {uid}')

        # Check if the account has the pwdAccountLockedTime attribute and remove if present.
        if 'pwdAccountLockedTime' in entry['attributes'] and entry['attributes']['pwdAccountLockedTime']:
            success = conn.modify(entry['dn'], {
                'pwdAccountLockedTime': [(MODIFY_DELETE, [entry['attributes']['pwdAccountLockedTime']]),],
            })

            # Failed to remove the locked time, raise exception as pwdPolicySubentry cannot/should not be
            # removed when associated attribute exists.
            if not success:
                logger.error(f'ldap, account unblock failed, could not delete pwdAccountLockedTime, username: {uid}')
                raise Exception(f'ldap, failed to unblock user, username: {uid}')

        # Remove pwdPolicySubentry (cn=disabled,ou=ppolicies,dc=example,dc=org), if present.
        if ('pwdPolicySubentry' in entry['attributes']
                and entry['attributes']['pwdPolicySubentry'] == settings.BITU_LDAP['ppolicy']):
            success = conn.modify(entry['dn'], {
                'pwdPolicySubentry': [(MODIFY_DELETE, [settings.BITU_LDAP['ppolicy']]),],
            })

            if not success:
                logger.error(f'ldap, account unblocked failed, could not delete pwdPolicySubentry, username: {uid}')
                raise Exception(f'ldap, failed to unblock user, username: {uid}')

        logger.info(f'ldap, account unblocked, username: {uid}')
