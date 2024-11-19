from typing import TYPE_CHECKING

import structlog

from .notification import send_permission_request_email


if TYPE_CHECKING:
    from permissions.models import Log, PermissionRequest

audit = structlog.getLogger('audit')


def permission_validation(sender, instance: 'Log', created: bool, **kwargs):
    instance.request.validate()

def request_validation(sender, instance: 'PermissionRequest', created: bool, **kwargs):
    if created:
        instance.validate()

def request_notification(sender, instance: 'PermissionRequest', created: bool, **kwargs):
    # Only notify when a permission request is created, not everytime it changes.
    # Only notify is the status is pending.
    if not created or instance.status != instance.PENDING:
        return

    send_permission_request_email(instance)


def permission_audit(sender, instance: 'Log', created: bool, **kwargs):
    if created:
        audit.info('log object created', id=instance.id, request=instance.request.id,
                   user=instance.created_by, approved=instance.approved, sender=sender)
