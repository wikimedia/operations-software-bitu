import logging

from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.module_loading import import_string


if TYPE_CHECKING:
    from .models import SSHKey


logger = logging.getLogger('bitu')


def update_ssh_key(sender, instance: 'SSHKey', created: bool, **kwargs):
    if not instance.system:
        return
    try:
        import_string(f'{instance.system}.helpers.syncronize_ssh_keys')(instance.user)
    except Exception:
        logger.warning(f'Error calling ssh key handler, \
                       instance: {instance.system}, user: {instance.user}, \
                       key_id: {instance.pk}')

    if created and instance.system == '':
        for system in settings.BITU_SUB_SYSTEMS:
            try:
                import_string(f'{system}.helpers.check_ssh_key')(instance)
            except Exception:
                logger.warning(f'ssh key configured tried to load unknown backend: {system}')
