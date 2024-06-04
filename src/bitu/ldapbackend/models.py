from typing import Dict, List


import bituldap

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def get_ldap_attributes_editable() -> List[Dict]:
    """Return a list of LDAP attributes that are to be
    presented as input fields in the UI.

    The returned list contains dictionaries which are required to contain at least
    a "name" key. It is assumed that all data types are strings as default. Any
    other datatype requirements must be handled using validators.


    The following fields may be used:
    * name       - Must correspond to the name of the attribute in LDAP.
    * display    - A "pretty print" version of the field name.
    * choices    - a set of sets (key and value) to be used to generate a ChoicesField,
                   rather than a textbox.
    * validators - List of validators to apply to the field, before allowing an update.
                   Validators must be a standard Django form field validator
                   (https://docs.djangoproject.com/en/3.2/ref/forms/validation/).

    Returns:
        List[Dict]: A list of dicts with the settings for the editable fields in the
                    LDAP editor.
    """
    options = settings.BITU_SUB_SYSTEMS.get(__name__.split('.')[0])
    editable = options.get('attributes', {}).get('edit', [])
    return editable


def get_ldap_attributes_view() -> List[Dict]:
    """Return a list of attributes from LDAP which are to be displayed
    to the user.

    This functions similarly to the get_ldap_attributes_editable() function,
    but fetches read-only fields. This is information the user is allowed to
    view, but not edit, this could be fields username, uidNumber or email.

    The following fields may be used:
    * name (required) - Must correspond to the name of the attribute in LDAP.
    * display         - A "pretty print" version of the field name.

    Returns:
        List[Dict]: A list of dicts with the settings for the read-only fields
                    in the LDAP editor.
    """
    options = settings.BITU_SUB_SYSTEMS.get(__name__.split('.')[0])
    return options.get('attributes', {}).get('view', [])  # - editable


def load_attribute_values(user: 'User', attributes: List[Dict]):
    user = bituldap.get_user(user.username)
    for attribute in attributes:
        attribute['value'] = getattr(user, attribute['name'], '')
    return attributes
