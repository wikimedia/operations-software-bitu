# SPDX-License-Identifier: GPL-3.0-or-later
import logging

import bituldap

from django.contrib import messages

from .jobs import update_ldap_attributes

logger = logging.getLogger('social')

def global_account_link(strategy, details, backend, user=None, *args, **kwargs):
    logger.debug(f'strategy: {strategy}, details: {details}, backend: {backend}, user: {user}, args: {args}, kwargs: {kwargs}')
    if not user:
        return

    if backend.name != 'mediawiki':
        return

    if 'userID' not in details:
        return

    # Enqueue LDAP attribute job.
    update_ldap_attributes.delay(user, {'wikimediaGlobalAccountId': details['userID'],
                                        'wikimediaGlobalAccountName': details['username']})

    # Flush messages, to ensure that our "please link accounts"
    # message is not present from previus validations.
    request = kwargs['request']
    storage = messages.get_messages(request)
    storage._queued_messages = []

    # The LDAP update is queued, but may not be stored when
    # rendering the next page. Set the session to indicate
    # that we expect the attribute to be successfully
    # updated in the near future.
    request.session['wikimedia_global'] = True