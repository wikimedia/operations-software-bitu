from typing import Any, Union
from django import forms
from django.conf import settings

from .models import SSHKey

class SSHKeyAssignmentForm(forms.ModelForm):
    system = forms.MultipleChoiceField(
        widget=forms.RadioSelect,
        choices=()
    )

    def __init__(self, *args, **kwargs):
        systems = [(k, k) for k, v in settings.BITU_SUB_SYSTEMS.items() if v.get('ssh_keys', {}).get('managed', False)]

        super().__init__(*args, **kwargs)
        self.fields['system'].choices = systems

    class Meta:
        model = SSHKey
        fields = ['system']