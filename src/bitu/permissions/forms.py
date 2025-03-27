from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import PermissionRequest


class PermissionRequestForm(ModelForm):

    class Meta:
        model = PermissionRequest
        fields = ['comment']
