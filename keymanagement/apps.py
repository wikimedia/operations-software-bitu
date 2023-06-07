from django.apps import AppConfig
from django.db.models.signals import post_save
from . import signals

class KeymanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'keymanagement'

    def ready(self) -> None:
        from .models import SSHKey
        from django.contrib.auth import get_user_model
        User = get_user_model()

        post_save.connect(signals.update_ssh_key, SSHKey)
        post_save.connect(signals.load_ssh_key, User)