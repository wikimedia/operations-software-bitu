from typing import Union

from django.conf import settings


def capitalize_first(username: str) -> str:
    # Do not be tempted to replace this function with capitalize or title.
    # These methods do not do the same thing. Capitalize will ensure
    # that the the first letter is upper-case, and the remaining is
    # lower-case, mangling "John Doe" into "John doe". The reverse is the
    # true for "title", "john doe" will be returned as "John Doe" and while
    # that may be what the user intended, we cannot be sure, nor may it be
    # applicable in all languages.
    if not username:
        return username

    if len(username) == 1:
        return username.upper()

    return username[0].upper() + username[1:]

def list_backends(**kwargs) -> dict[str, str]:
    """Return a list of backends.
    Returns all available backends, or a filtered result based on the provided
    kwargs. E.g. providing manage_ssh_keys=True will filter out any backend
    which does not have the attribute manage_ssh_keys set to True.

    Default returns an unfiltered result.

    Returns:
        dict[str, str]: key, display name for the backend.
    """
    backend = {}
    for k,v in settings.BITU_SUB_SYSTEMS.items():
        # Loop through the provided key/value pairs and match
        # them of attributes/dict entries in the backend configuration.
        valid = True
        for attr, value in kwargs.items():
            # Attribute not present or found with incorrect value.
            # mark as invalid and skip further evaluation.
            if attr not in v or v[attr] != value:
                valid = False
                continue

        # If filter invalided backend entry, continue to the next.
        # Otherwise add to list of backends to return.
        if not valid:
            continue

        # TODO: Should probably be renamed to "display_name"
        if 'ssh_keys_display_name' in v:
            backend[k] = v['ssh_keys_display_name']
        else:
            backend[k] = k
    return backend