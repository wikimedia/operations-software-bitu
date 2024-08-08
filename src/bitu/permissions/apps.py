from django.apps import AppConfig
from django.db.models.signals import post_save

from .signals import permission_validation


class PermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'permissions'

    def ready(self) -> None:
        from permissions.models import Log
        post_save.connect(permission_validation, Log)
