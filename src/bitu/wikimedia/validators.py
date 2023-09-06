import logging

from typing import Tuple, TYPE_CHECKING

import bituldap

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    User = get_user_model()


logger = logging.getLogger('bitu')


def wikimedia_global_account(request: HttpRequest, user:'User') -> bool:
    """Check if a Wikimedia Global Account (SUL) have already been queried.

    Note that a HttpRequest is required as a session cookie is being set.
    The cookie ensures that LDAP is not queries on all requests. This
    happens because the function is intended to be used as part of a
    middleware function.

    Args:
        request: Django HttpRequest
        user: Django User object

    Returns:
        bool: Account has been linked True/False
    """

    # Check that the user has not previously dismissed
    # the request to link accounts.
    if request.COOKIES.get('wmf_link', False):
        return True

    # The user should be authenticated at this point
    # but let's check. If anonymous, lie and say that
    # the user isn't required to link the accounts.
    if user.is_anonymous:
        return True

    # Use session storage to avoid querying LDAP more
    # than we need to.
    if request.session.get('wikimedia_global', False):
        return True

    ldap_user = bituldap.get_user(user.get_username())
    if not ldap_user:
        logger.warning(f'wikimedia global account validation failure, error getting ldap user: {user.get_username()}')
        return True

    if not getattr(ldap_user, 'wikimediaGlobalAccountId', False):
        return False

    # User has already linked their accounts.
    request.session['wikimedia_global'] = True
    return True