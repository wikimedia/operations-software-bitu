import random
from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.forms import ModelForm
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from captcha.fields import CaptchaField
from captcha.fields import CaptchaTextInput

from .models import Signup


mark_safe_lazy = lazy(mark_safe, str)

# Generate challanges with a limited alphabet, but
# avoid characthers that look similar to confuse
# users.
def captcha_input_generator():
    lenght = getattr(settings, 'CAPTCHA_LENGTH', 5)
    alphabet = 'abcedefghkmnprstwxyz23456789'
    challenge = ''.join(random.sample(alphabet, lenght))
    return (challenge, challenge)


class SignupForm(ModelForm):
    captcha = CaptchaField(
        help_text=mark_safe_lazy(_('Learn more about <a href="https://en.wikipedia.org/wiki/CAPTCHA">CAPTCHAs</a>')))
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
        help_text="It is recommended to use a unique password that you are not using on any other website.",
    )
    password2 = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add codex stylesheet class.
        for field_name in self.fields:
            field = self.fields[field_name]
            field.widget.attrs['class'] = 'cdx-text-input__input'
            field.widget.attrs['aria-describedby'] = f'cdx-{field_name}'

        self.fields['username'].widget.attrs['placeholder'] = _('Username')
        self.fields['username'].widget.attrs['autocomplete'] = 'off'
        self.fields['username'].widget.attrs['max_length'] = 150
        self.fields['uid'].widget.attrs['placeholder'] = _('Type your username')
        self.fields['uid'].widget.attrs['autocomplete'] = 'off'
        self.fields['uid'].widget.attrs['max_length'] = 32
        self.fields['email'].widget.attrs['placeholder'] = _('example@email.org')
        self.fields['captcha'].widget.attrs['placeholder'] = _('Enter captcha text')
        self.fields['password1'].widget.attrs['placeholder'] = _('Unique password')
        self.fields['password2'].widget.attrs['placeholder'] = _('Confirm password')

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
        signup: Signup = super().save(commit=False)
        if commit:
            signup.save()

        signup.set_password(self.cleaned_data.get("password1"))
        signup.send_activation_link()
        return signup

    class Meta:
        model = Signup
        fields = ['username', 'uid', 'email']


class SignupActivationForm(ModelForm):
    is_active = forms.BooleanField(widget=forms.HiddenInput())

    class Meta:
        model = Signup
        fields = ['is_active']
