from django.conf import settings
from django.core.exceptions import ValidationError
from paramiko.pkey import PublicBlob

from .helpers import ssh_key_string_to_object

class SSHKeyValidator:
    def validate(self, ssh_key):
        if 'BEGIN RSA PRIVATE KEY' in ssh_key or  'BEGIN OPENSSH PRIVATE KEY' in ssh_key:
            raise ValidationError(f'This is a private key. Private keys should never be shared or uploaded anywhere.')
        try:
            pkey: PublicBlob = PublicBlob.from_string(ssh_key)
        except:
            raise ValidationError(f'Invalid key. Input was not a valid public SSH key.')

        # If no special rules are configured, allow all valid keys.
        allowed_key_types = getattr(settings, 'BITU_SSH_KEY_VALIDATOR',{}).get('allowed_key_type', {})
        if not allowed_key_types:
            return

        if pkey.key_type not in allowed_key_types.keys():
            key_names = ','.join(allowed_key_types.keys())
            raise ValidationError(f'Key type {pkey.key_type} is insecure. Supported keys are: {key_names}')

        key_type = allowed_key_types[pkey.key_type]
        if pkey.key_type == 'ssh-rsa' and 'min_key_size' in key_type:
            required_key_size = key_type['min_key_size']

            # Split up the SSH key to remove type and comment at the front and end.
            # base64 decode and parse to RSAKey constructor as data. Then get number
            # of bits / key size from RSAKey object.
            obj = ssh_key_string_to_object(ssh_key)
            key_size = obj.get_bits()
            if  key_size < required_key_size:
                raise ValidationError(f'Minimum key size for SSH keys of the type: rsa is {required_key_size}, upload key was: {key_size}')



    def get_help_text(self):
        return (
            "Invalid key, don't know why"
        )

ssh_key_validator = SSHKeyValidator()