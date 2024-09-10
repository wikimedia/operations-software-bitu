from django.apps import AppConfig
from django.db.models.signals import post_save


from .signals import permission_audit, permission_validation, request_notification


class PermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'permissions'

    def ready(self) -> None:
        from permissions.models import Log, PermissionRequest
        post_save.connect(permission_audit, Log)
        post_save.connect(permission_validation, Log)
        post_save.connect(request_notification, PermissionRequest)
