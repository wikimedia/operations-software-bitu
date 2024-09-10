import logging

from typing import TYPE_CHECKING

import bituldap

from django_rq import job
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import QuerySet
from django.template.loader import get_template
from django.urls import reverse

if TYPE_CHECKING:
    from .models import PermissionRequest

logger = logging.getLogger('bitu')


def load_templates() -> dict[str:str]:
    """Load template configuration for settings.

    Returns:
        dict: Template for each supported format, currently only plaintext.
    """
    name = settings.BITU_NOTIFICATION.get('pending_permissions_template_prefix', 'pending_manager_approval')
    plaintext = f'permissions/email/{name}.txt'
    return {'plaintext': get_template(plaintext), }


def get_managers(request: 'PermissionRequest') -> set[str]:
    """Find all managers who can approve a given request for additional permissions.

    Args:
        request (PermissionRequest): Bitu PermissionRequest object

    Returns:
        set[str]: Usernames for approving managers.
    """
    managers = []
    rules = settings.ACCESS_REQUEST_RULES.get(request.system, {}).get(request.key.lower(), [])
    for rule in rules:
        managers.extend(rule.get('managers', []))
    return set(managers)


def get_permission_for_manager(username: str) -> list[set[str, str]]:
    """Return all permissions a given manager can approve.

    Args:
        username (str): Manager username

    Returns:
        list[set[str, str]]: List of systems and permissions,
                             each set has a system as index zero
                             and the permission key and index one.
    """
    permissions = []
    for system, backend in settings.ACCESS_REQUEST_RULES.items():
        for key, rules in backend.items():
            for rule in rules:
                if username in rule.get('managers', []):
                    permissions.append((system, key))
    return permissions


def get_pending_requests(username: str) -> QuerySet:
    """Get all pending permission requests for a given username

    Args:
        username (str): Manager username

    Returns:
        QuerySet: PermissionRequests as a Django queryset.
    """
    from .permission import PermissionRequest
    permissions = get_permission_for_manager(username)
    requests = []

    # A little hacky: Iterate over all the permissions managed by that username,
    # build a list of PermissionRequest IDs currently pending for those system/key
    # combinations. Then use those IDs to get a deduplicated QuerySet.
    for permission in permissions:
        requests.extend(PermissionRequest.objects.filter(
            system=permission[0],
            key=permission[1],
            status=PermissionRequest.PENDING).values_list('id', flat=True))

    # Filter out all none pending requests.
    return PermissionRequest.objects.filter(id__in=requests, status=PermissionRequest.PENDING)


@job('notification')
def send_permission_request_email(request: 'PermissionRequest') -> None:
    """Given a request for new permissions, notify all managers of that permission
    about their list of pending request.

    Args:
        request (PermissionRequest): Bitu PermissionRequest object.
    """

    managers = get_managers(request)
    logger.info(
        f'email notification triggered by permission request, permission_request:{request.pk}, \
user: {request.user}, \
managers: {",".join(managers)}')

    # Get full URI for pending list
    uri = settings.BITU_DOMAIN + reverse('permissions:pending')
    templates = load_templates()

    subject = settings.BITU_NOTIFICATION.get('pending_permission_request_subject',
                                             'Bitu IDM - Pending permission requests')
    from_email = settings.BITU_NOTIFICATION['default_sender']

    # Loop over all managers, rather than adding multiple receipients to one email.
    # This is done because we include all permissions currently pending our approval, but
    # those may not be the same for all managers.
    for manager in managers:
        # Don't notify ourselves, if we happen to be managing the permission we're applying for.
        # Users cannot approve their own requests.
        if manager == request.user.get_username():
            continue

        # Load email from LDAP, as we cannot be sure that the manager has
        # signed in before.
        to_email = bituldap.get_user(manager).mail
        requests = get_pending_requests(manager)
        context = {'uri': uri, 'requests': requests}
        msg = EmailMultiAlternatives(
            subject,
            templates['plaintext'].render(context),
            from_email,
            [to_email])
        msg.send()
        logger.info(
            f'email pending requests for {manager}, email: {to_email}, requests pending: {len(requests)}'
        )
