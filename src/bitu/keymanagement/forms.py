from typing import Any, Union
from django import forms
from django.conf import settings

from .models import SSHKey


class SSHKeyCreateForm(forms.ModelForm):
    class Meta:
        model = SSHKey
        fields = ('comment', 'ssh_public_key')
        widgets = {
            'comment': forms.TextInput(attrs={'size': 96}),
            'ssh_public_key': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
        }


class SSHKeyActivateFormSingle(forms.ModelForm):
    class Meta:
        model = SSHKey
        fields = ('system',)
        widgets = {
            'system': forms.Select() if len(SSHKey.systems) > 1 else forms.HiddenInput()
        }