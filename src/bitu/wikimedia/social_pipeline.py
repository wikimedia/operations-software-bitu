# SPDX-License-Identifier: GPL-3.0-or-later
import logging

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .jobs import update_ldap_attributes

logger = logging.getLogger('social')

def global_account_link(strategy, details, backend, user=None, *args, **kwargs):
    """Social Auth pipeline function for linking a MediaWiki account.

    The pipeline function will intercept a callback from an OAuth authentication
    request against MediaWiki and link the user account ID to the currently logged
    in user.

    .. code-block:: python

        SOCIAL_AUTH_PIPELINE = (
            'social_core.pipeline.social_auth.social_details',
            ...
            'social_core.pipeline.user.user_details',
        )

    Args:
        strategy: Social Auth strategy (which gives access to current store, backend and request).
        details: User details given by authentication provider
        backend: The backend handling the authentication, we accept only mediawiki.
        user: Django user object. Defaults to None.
    """
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

    # The LDAP update is queued, but may not be stored when
    # rendering the next page. Set the session to indicate
    # that we expect the attribute to be successfully
    # updated in the near future.
    request = kwargs['request']
    request.session['wikimedia_global'] = True
    messages.success(request, _("Accounts successfully linked. Please allow for a few minutes for the change to propagate."))