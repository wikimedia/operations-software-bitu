from typing import TYPE_CHECKING

from .notification import send_permission_request_email

if TYPE_CHECKING:
    from permissions.models import PermissionRequest


def permission_validation(sender, instance: 'PermissionRequest', created: bool, **kwargs):
    instance.request.validate()


def request_notification(sender, instance: 'PermissionRequest', created: bool, **kwargs):
    # Only notify when a permission request is created, not everytime it changes.
    # Only notify is the status is pending.
    if not created or instance.status != instance.PENDING:
        return

    send_permission_request_email(instance)
