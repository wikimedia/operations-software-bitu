from typing import Union

import logging
import bituldap

from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.module_loading import import_string
from ldap3 import Entry

from .models import get_ldap_attributes_editable

logger = logging.getLogger('bitu')

def load_validator(attr):
    modules = attr.get('validators', [])
    validators = []
    for module in modules:
        try:
            validators.append(import_string(modules))
        except:
            logger.warning(f'ldap attribute editor attempted to load unknown validator: {module}')

    return validators


class LDAPUserForm(forms.Form):
    default_allow_list = ['sn', 'givenName']
    def __init__(self, uid, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user: Union[Entry, None] = bituldap.get_user(uid)
        self.allow_list = get_ldap_attributes_editable()
        if not self.user:
            raise ObjectDoesNotExist(uid)

        self.id_list = []
        self.editable = get_ldap_attributes_editable()
        for attr in self.editable:
            if not hasattr(self.user, attr['name']):
                continue

            self.id_list.append(attr['name'])
            validators = load_validator(attr)
            value = getattr(self.user, attr['name'], '')
            if value:
                value = value.value

            if 'choices' in attr:

                field = forms.ChoiceField(label=attr['display'],
                                        required=True,
                                        initial=value,
                                        choices=attr['choices'],
                                        validators=validators)
            else:
                field = forms.CharField(label=attr['display'],
                                        required=True,
                                        initial=value,
                                        validators=validators)
            self.fields[attr['name']] = field

    def save(self) -> bool:
        if not self.is_valid() or not self.user:
            return False

        if not self.has_changed:
            return True

        for name, value in self.cleaned_data.items():
            setattr(self.user, name, value)

        return self.user.entry_commit_changes()
