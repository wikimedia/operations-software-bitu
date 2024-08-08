from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from permissions.models import PermissionRequest


def permission_validation(sender, instance: 'PermissionRequest', created: bool, **kwargs):
    instance.request.validate()
