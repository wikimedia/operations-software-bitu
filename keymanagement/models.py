from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from .validators import ssh_key_validator

User = get_user_model()


class SSHKey(models.Model):
    systems = [
        (k, v.get('ssh_keys_display_name', k))
        for k, v in settings.BITU_SUB_SYSTEMS.items() if v.get('manage_ssh_keys', False)
    ]
    systems.append(('',''))
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ssh_keys')
    system = models.CharField(max_length=256, choices=systems, default='')
    ssh_public_key = models.TextField(unique=True, validators=(ssh_key_validator.validate,))
    comment = models.CharField(max_length=256, default='')
    active = models.BooleanField(default=False)
    key_type = models.CharField(max_length=32, default='', null=True)
    key_size = models.IntegerField(default=0)

    @property
    def key_as_byte_string(self):
        return bytes(self.ssh_public_key, 'utf-8')

    def get_display(self):
        if len(self.ssh_public_key) <= 100:
            return self.ssh_public_key

        # For display purposes viewing the entire key isn't required and will
        # make layouting harder. Truncate the key to 125 characters, consisting
        # of the first 80, a separator and the last 80.
        return self.ssh_public_key[0:20] + ' ... ' + self.ssh_public_key[-80:]

    def __str__(self) -> str:
        return self.get_display()

    class Meta:
        unique_together = ('user', 'system', 'active', 'ssh_public_key')
