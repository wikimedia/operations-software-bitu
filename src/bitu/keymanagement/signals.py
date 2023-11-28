import logging

from typing import NewType, TYPE_CHECKING

from django.conf import settings
from django.utils.module_loading import import_string


if TYPE_CHECKING:
    from .models import SSHKey
    from django.contrib.auth import get_user_model
    User = NewType('User', get_user_model())

logger = logging.getLogger('bitu')


def load_ssh_key(sender, instance: 'User', created: bool, **kwargs):
    for system in settings.BITU_SUB_SYSTEMS:
        try:
            load_ssh_key = import_string(f'{system}.helpers.load_ssh_key')
            load_ssh_key(instance)
        except:
            pass


def update_ssh_key(sender, instance: 'SSHKey', created: bool, **kwargs):
    if not instance.system:
        return
    try:
        import_string(f'{instance.system}.helpers.syncronize_ssh_keys')(instance.user)
    except:
        logger.warning(f'Error calling ssh key handler, instance: {instance.system}, user: {instance.user}, key_id: {instance.pk}')

    if created and instance.system == '':
        for system in settings.BITU_SUB_SYSTEMS:
            try:
                import_string(f'{system}.helpers.check_ssh_key')(instance)
            except:
                logger.warning(f'ssh key configured tried to load unknown backend: {system}')
