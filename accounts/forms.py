from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User

class UpdateEmailForm(forms.Form):
    email1 = forms.EmailField(label=_('New email'))
    email2 = forms.EmailField(label=_('Confirm email'))

    def clean_email2(self):
        email1 = self.cleaned_data.get("email1")
        email2 = self.cleaned_data.get("email2")
        if email1 and email2 and email1 != email2:
            raise ValidationError(
                self.error_messages["email_mismatch"],
                code="email_mismatch",
            )
        return email2


class VerifyEmailForm(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    email = forms.EmailField(widget=forms.HiddenInput())
