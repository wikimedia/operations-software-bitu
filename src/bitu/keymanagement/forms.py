from django import forms

from .models import SSHKey


class SSHKeyCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add codex stylesheet class.
        for field_name in self.fields:
            field = self.fields[field_name]
            field.widget.attrs['class'] = 'cdx-text-input__input'
            field.widget.attrs['aria-describedby'] = f'cdx-{field_name}'

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
