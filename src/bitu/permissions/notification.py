import logging

from typing import TYPE_CHECKING, Iterator

import bituldap

from django_rq import job
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import QuerySet
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


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


def get_user_dns_from_ldap_group(group_dns: list[str]) -> set[str]:
    """Fetch uids for all members of an LDAP group

    Args:
        group_dn (str): LDAP CN for group/groupOfNames

    Returns:
        set[str]: set of user DNs
    """
    members = []
    for cn in group_dns:
        # Get group name from DN
        name = cn.split(',')[0].split('=')[1]
        members.extend([m for m in bituldap.get_group(name).member])


    # Convert to set to strip duplicates.
    return set(members)


def get_notification_email_for_users(users: Iterator[str]) -> set[str]:
    emails = []
    for user in users:
        # Get uid from DN
        uid = user.split(',')[0][4:]

        user = bituldap.get_user(uid)
        if user is None:
            continue

        # Because we're going to convert the resulting list to a set, get
        # the value/email as a string, rather than a Writeable/Readable LDAP
        # attribute, which cannot be hashed and automatically converted to a set.
        emails.append(user.mail.value)
    return set(emails)


def get_manager_emails(request: 'PermissionRequest') -> set[str]:
    """Find the email address for all who can approve a given request for additional permissions.

    Args:
        request (PermissionRequest): Bitu PermissionRequest object

    Returns:
        set[str]: email for approving managers.
    """
    managers = []
    rules = settings.ACCESS_REQUEST_RULES.get(request.system, {}).get(request.key, [])
    for rule in rules:
        managers.extend(rule.get('notify', []))
        manager_dns = get_user_dns_from_ldap_group(rule.get('notify_group', []))
        managers.extend(get_notification_email_for_users(manager_dns))

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

    managers = get_manager_emails(request)
    if not managers:
        return

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
        if manager == request.user.email:
            continue

        # Load email from LDAP, as we cannot be sure that the manager has
        # signed in before.
        to_email = manager
        context = {'uri': uri, 'request': request}
        msg = EmailMultiAlternatives(
            subject,
            templates['plaintext'].render(context),
            from_email,
            [to_email])
        msg.send()
        logger.info(
            f'email pending requests for {manager}, email: {to_email}, request pending: {request.id}'
        )


@job('notification')
def send_permission_status_change_email(request: 'PermissionRequest') -> None:
    template_base = 'permissions/email/request_approved' if request.status == request.APPROVED else 'permissions/email/request_rejected'
    context = {'request': request}
    plaintext = get_template(template_base + '.txt').render(context)
    html = get_template(template_base + '.html').render(context)

    msg = EmailMultiAlternatives(
        subject=_(
            "Request for access to %(permission)s as been %(state)s.") % {
                "permission": request.permission.name,
                "state": request.status.lower()
            },
        body=plaintext,
        from_email=settings.BITU_NOTIFICATION['default_sender'],
        to=[request.user.email])
    msg.attach_alternative(html, "text/html")
    msg.send()

