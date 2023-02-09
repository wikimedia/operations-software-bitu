
import logging

from typing import Dict

import bituldap

from django.contrib.auth import get_user_model
from django_rq import job


logger = logging.getLogger('bitu')
User = get_user_model()


@job
def update_ldap_attributes(user:'User', attributes:Dict):
    ldap_user = bituldap.get_user(user.get_username())
    if not ldap_user:
        logger.warning(f'user: {user.get_username()} not found in ldap')
        return

    for k,v in attributes.items():
        setattr(ldap_user, k, v)

    ldap_user.entry_commit_changes()
    logger.info(f'update ldap user: {ldap_user} with attributes: {attributes}')
