from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from sshpubkeys import SSHKey as SSHPublicKey
from sshpubkeys.exceptions import InvalidKeyError

from .helpers import key_type_from_str, ssh_key_string_to_object
from .validators import ssh_key_validator, ssh_key_usage_validator


User = get_user_model()


class SSHKey(models.Model):
    systems = [
        (k, v.get('ssh_keys_display_name', k))
        for k, v in settings.BITU_SUB_SYSTEMS.items() if v.get('manage_ssh_keys', False)
    ]

    # Build help text for SSH key input field.
    allowed_key_types = getattr(settings, 'BITU_SSH_KEY_VALIDATOR', {}).get('allowed_key_type', {})
    ssh_public_key_help = [
        _('Please consult our documentation if you need help generating your SSH keys, \
          available at: <a href="https://wikitech.wikimedia.org/wiki/Generate_an_SSH_Key"').__str__(),
        _('Valid key types are: %s' % ', '.join(allowed_key_types)).__str__()
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ssh_keys')
    system = models.CharField(max_length=256, choices=systems, blank=False, default=systems[0][0])
    ssh_public_key = models.TextField(
        unique=True,
        validators=(ssh_key_validator, ssh_key_usage_validator))
    comment = models.CharField(max_length=256, default='')
    active = models.BooleanField(default=False)
    key_type = models.CharField(max_length=32, default='', null=True)
    key_size = models.IntegerField(default=0)

    # Allow users to indicte that signals should not be processed.
    # Syncronisation with backend can result in further calls to the
    # SSHKey save method, which in term triggers the signals again.
    _skip_signal = False

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        self.ssh_public_key = self.ssh_public_key.strip()
        obj: SSHPublicKey = SSHPublicKey(keydata=self.ssh_public_key)
        try:
            obj.parse()
            self.key_size = obj.bits
            self.key_type = obj.key_type.decode('utf8')
        except (InvalidKeyError, NotImplementedError):
            pass

    @property
    def key_as_byte_string(self):
        return bytes(self.ssh_public_key, 'utf-8')

    def get_display(self):
        if len(self.ssh_public_key) <= 100:
            return self.ssh_public_key

        # For display purposes viewing the entire key isn't required and will
        # make layouting harder. Truncate the key to 125 characters, consisting
        # of the first 80, a separator and the last 80.
        short_form = self.ssh_public_key[0:20] + ' ... ' + self.ssh_public_key[-80:]
        return short_form if len(short_form) < len(self.ssh_public_key) else self.ssh_public_key

    def get_finger_print(self) -> str:
        obj = SSHPublicKey(keydata=self.ssh_public_key)

        try:
            obj.parse()
            return obj.hash_sha512()
        except Exception:
            return ''

    def __str__(self) -> str:
        return self.get_display()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['system', 'ssh_public_key', 'active'],
                name='unique_active_key'
            ),]
