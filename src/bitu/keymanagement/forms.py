from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _


from .models import SSHKey


class SSHKeyCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add codex stylesheet class.
        for field_name in self.fields:
            field = self.fields[field_name]
            field.widget.attrs['class'] = 'cdx-text-input__input'
            field.widget.attrs['aria-describedby'] = f'cdx-{field_name}'

        allowed_key_types = getattr(settings, 'BITU_SSH_KEY_VALIDATOR',{}).get('allowed_key_type', {})


        help_messages = [
            _('Please consult our documentation if you need help generating your SSH keys, \
              available at: <a href="https://wikitech.wikimedia.org/wiki/Generate_an_SSH_Key"> \
              https://wikitech.wikimedia.org/wiki/Generate_an_SSH_Key</a>').__str__(),
            _("Valid SSH key types are %(key_types)s" % {"key_types": ', '.join(allowed_key_types.keys())}).__str__(),
        ]

        self.fields['ssh_public_key'].help_text = mark_safe('<br />'.join(help_messages))

    class Meta:
        model = SSHKey
        fields = ('comment', 'ssh_public_key', 'system')
        widgets = {
            'comment': forms.TextInput(attrs={'size': 96}),
            'ssh_public_key': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
        }


class SSHKeyActivateFormSingle(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add codex stylesheet class.
        for field_name in self.fields:
            field = self.fields[field_name]
            field.widget.attrs['aria-describedby'] = f'cdx-{field_name}'

            if isinstance(field, forms.ChoiceField):
                field.widget.attrs['class'] = 'cdx-select'
            elif isinstance(field, forms.HiddenInput):
                pass
            else:
                field.widget.attrs['class'] = 'cdx-text-input__input'

    class Meta:
        model = SSHKey
        fields = ('system',)
