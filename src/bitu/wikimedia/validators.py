import logging


import bituldap

from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger('bitu')


def wikimedia_global_account(request: HttpRequest) -> bool:
    """Check if a Wikimedia Global Account (SUL) linking is desired.

    Note that a HttpRequest is required as a session cookie is being set.
    The cookie ensures that LDAP is not queried on all requests. This
    is required as there might be a small delay between linking and LDAP
    being updated. Querying the session cookie also allows users to
    acknowledge the banner, but not actually link the accounts.

    This feature can be disabled completely by setting:
    WIKIMEDIA_GLOBAL_ACCOUNT_LINKING = False in the configuration.

    Args:
        request: Django HttpRequest

    Returns:
        bool: Account has been linked True/False
    """

    # Account linking can be disabled completely in settings
    if hasattr(settings, "WIKIMEDIA_GLOBAL_ACCOUNT_LINKING") and not settings.WIKIMEDIA_GLOBAL_ACCOUNT_LINKING:
        # Account linking disabled, lie and suggest that the account is already linked,
        # to hide the message box nagging the user to link.
        return True

    # Check that the user has not previously dismissed
    # the request to link accounts.
    if request.COOKIES.get('wmf_link', False):
        return True

    # The user should be authenticated at this point
    # but let's check. If anonymous, lie and say that
    # the user isn't required to link the accounts.
    if request.user.is_anonymous:
        return True

    # Use session storage to avoid querying LDAP more
    # than we need to.
    if request.session.get('wikimedia_global', False):
        return True

    ldap_user = bituldap.get_user(request.user.get_username())
    if not ldap_user:
        logger.warning(f'wikimedia global account validation failure, error getting ldap user: {request.user.get_username()}')
        return True

    if not getattr(ldap_user, 'wikimediaGlobalAccountId', False):
        return False

    # User has already linked their accounts.
    request.session['wikimedia_global'] = True
    return True


def phabricator_account(request: HttpRequest) -> bool:
    """Check if a Phabricator account linking is desired.

    Note that a HttpRequest is required as a session cookie is being set.
    The cookie ensures that LDAP is not queried on all requests. This
    is required as there might be a small delay between linking and LDAP
    being updated. Querying the session cookie also allows users to
    acknowledge the banner, but not actually link the accounts.

    This feature can be disabled completely by setting:
    PHABRICATOR_ACCOUNT_LINKING = False in the configuration.

    Args:
        request: Django HttpRequest

    Returns:
        bool: Account has been linked True/False
    """

    # Account linking can be disabled completely in settings
    if hasattr(settings, "PHABRICATOR_ACCOUNT_LINKING") and not settings.PHABRICATOR_ACCOUNT_LINKING:
        # Account linking disabled, lie and suggest that the account is already linked,
        # to hide the message box nagging the user to link.
        return True

    # Check that the user has not previously dismissed
    # the request to link accounts.
    if request.COOKIES.get('wmf_phab_link', False):
        return True

    # The user should be authenticated at this point
    # but let's check. If anonymous, lie and say that
    # the user isn't required to link the accounts.
    if request.user.is_anonymous:
        return True

    # Use session storage to avoid querying LDAP more
    # than we need to.
    if request.session.get('phabricator_account', False):
        return True

    ldap_user = bituldap.get_user(request.user.get_username())
    if not ldap_user:
        logger.warning(f'wikimedia global account validation failure, error getting ldap user: {request.user.get_username()}')
        return True

    if not getattr(ldap_user, 'phabricatorAccountID', False):
        return False

    # User has already linked their accounts.
    request.session['phabricator_account'] = True
    return True