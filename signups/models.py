# SPDX-License-Identifier: GPL-3.0-or-later
import uuid

from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from .tokens import SignupActivationTokenGenerator, default_token_generator

from . import jobs

username_validators = []

username_validators = [import_string(module) for module in getattr(settings, 'SIGNUP_USERNAME_VALIDATORS', [])]


class Signup(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer."
        ),
        validators=username_validators,
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_("email address"), unique=True)

    def set_password(self, password):
        for name, module in settings.BITU_SUB_SYSTEMS.items():
            hash_func = import_string(module['password_hash'])

            sp = SignupPassword()
            sp.signup = self
            sp.module = name
            sp.value = hash_func(password)
            sp.save()

    def generate_activation_token(self):
        gen: SignupActivationTokenGenerator = default_token_generator
        token = gen.make_token(self)
        return token

    def validate_activation_token(self, token: str) -> bool:
        gen: SignupActivationTokenGenerator = default_token_generator
        valid = gen.check_token(self, token)
        return valid

    def send_activation_link(self):
        jobs.send_activation_email.delay(self)


class SignupPassword(models.Model):
    signup = models.ForeignKey(Signup, on_delete=models.CASCADE)
    module = models.CharField(null=False, max_length=150)
    value = models.CharField(max_length=256)
