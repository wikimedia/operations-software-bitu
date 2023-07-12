from django import forms
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class ForgotUsernameForm(forms.Form):
    email = forms.EmailField()

class RequestPasswordResetForm(forms.Form):
    username = forms.CharField(max_length=256)


class PasswordResetForm(forms.Form):
    error_messages = {
        "password_mismatch": _("The two password fields didn’t match."),
    }
    required_css_class = "required"
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password"}
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        password_validation.validate_password(password2)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data.get("password1")
