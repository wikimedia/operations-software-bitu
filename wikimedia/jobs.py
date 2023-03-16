
import base64
import logging

from typing import Dict, Union

import bituldap

from django.contrib.auth import get_user_model
from django.urls import reverse
from django_rq import job
from ldap3 import Entry

from .tokens import default_token_generator

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

@job('notification')
def send_email_password_reset(username):
    ldap_user: Union[Entry, None] = bituldap.get_user(username)
    if not ldap_user:
        return

    token = default_token_generator.make_token(ldap_user)
    uid = base64.b64encode(bytes(ldap_user.uid.value, 'utf8'))
    url = reverse('wikimedia:reset', kwargs={'token': token, 'uidb64': uid.decode(encoding='utf8')})
    print(url)

