from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from bitu.forms import GenericCodexForm

from .models import SecurityToken


class UpdateEmailForm(GenericCodexForm):
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


class VerifyEmailForm(GenericCodexForm):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    email = forms.EmailField(widget=forms.HiddenInput())


class TokenForm(GenericCodexForm):
    comment = forms.CharField(max_length=256)


class SecurityTokenForm(GenericCodexForm):
    security_token = forms.CharField(widget=forms.HiddenInput)
    username = forms.CharField(widget=forms.HiddenInput)
    validation_code = forms.CharField()

    def clean_validation_code(self):
        token = self.cleaned_data.get('security_token')
        username = self.cleaned_data.get('username')
        code = self.cleaned_data.get('validation_code')
        try:
            st = SecurityToken.objects.get(pk=token, user__username=username)
        except SecurityToken.DoesNotExist:
            raise ValidationError(
                'Invalid code',
                code='validation_code_invalid'
            )

        if not st.validate(code):
            raise ValidationError(
                'Invalid code',
                code='validation_code_invalid'
            )

        st.enabled = True
        st.save()
        return code


class SecurityTokenDeleteForm(SecurityTokenForm):
    def clean_validation_code(self):
        token = self.cleaned_data.get('security_token')
        username = self.cleaned_data.get('username')
        code = super().clean_validation_code()
        if code:
            SecurityToken.objects.get(pk=token, user__username=username).delete()
        return code
