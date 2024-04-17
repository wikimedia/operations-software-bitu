import base64
import logging

from typing import NewType, TYPE_CHECKING

from django.conf import settings
from django.utils.module_loading import import_string

from paramiko.dsskey import DSSKey
from paramiko.ecdsakey import ECDSAKey
from paramiko.ed25519key import Ed25519Key
from paramiko.pkey import PKey, PublicBlob
from paramiko.rsakey import RSAKey


if TYPE_CHECKING:
    from django.contrib.auth import get_user_model
    User = NewType('User', get_user_model())

logger = logging.getLogger('bitu')


def ssh_key_without_comment(ssh_key: str) -> str:
    # Example: '      ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAkTVYhMVOooNQwfxURKnFYav/huLuSh3B+vFiLm4UrL Bitu ED25519 Test Key 3'  # noqa
    #          |strip| element 0 |                          element 1                                 |       discard         |  # noqa
    # When joining element 0 and 1 use array slicing to getting two elements, starting from index 0.
    # Expected result: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAkTVYhMVOooNQwfxURKnFYav/huLuSh3B+vFiLm4UrL
    elements = ssh_key.strip().split(' ')
    return ' '.join(elements[0:2])


def ssh_key_string_to_object(ssh_key: str) -> PKey:
    sanitized_key_data = ssh_key.strip()
    blob = PublicBlob.from_string(sanitized_key_data)

    key = PKey()
    data = base64.b64decode(sanitized_key_data.split(' ', 3)[1])
    if blob.key_type == 'ssh-dss':
        key = DSSKey(data=data)
    elif blob.key_type == 'ssh-rsa':
        key = RSAKey(data=data)
    elif blob.key_type == 'ssh-ecdsa':
        key = ECDSAKey(data=data)
    elif blob.key_type == 'ssh-ed25519':
        key = Ed25519Key(data=data)

    return key


def key_type_from_str(ssh_key) -> str:
    blob = PublicBlob.from_string(ssh_key)
    return blob.key_type


def load_ssh_key(user: 'User'):
    """load ssh keys from various subsystems for the given user

    Args:
        user (User): Django user object
    """
    for system in settings.BITU_SUB_SYSTEMS:
        try:
            import_string(f'{system}.jobs.load_ssh_key')(user)
        except ImportError:
            logger.debug(f'backend does not support key management, system:{system}')
        except Exception as e:
            logger.error(f'error importing ssh keys, system:{system}, user: {user.get_username()}, exception: {e}')
