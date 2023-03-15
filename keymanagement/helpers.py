import base64

from paramiko.dsskey import DSSKey
from paramiko.ecdsakey import ECDSAKey
from paramiko.ed25519key import Ed25519Key
from paramiko.pkey import PKey, PublicBlob
from paramiko.rsakey import RSAKey

def ssh_key_string_to_object(ssh_key) -> PKey:
    blob = PublicBlob.from_string(ssh_key)

    key = PKey()
    data = base64.b64decode(ssh_key.split(' ', 3)[1])
    if blob.key_type == 'ssh-dss':
        key = DSSKey(data=data)
    elif blob.key_type == 'ssh-rsa':
        key = RSAKey(data=data)
    elif blob.key_type == 'ssh-ecdsa':
        key = ECDSAKey(data=data)
    elif blob.key_type == 'ssh-ed25519':
        key = Ed25519Key(data=data)
    return key

