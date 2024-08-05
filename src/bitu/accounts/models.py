# SPDX-License-Identifier: GPL-3.0-or-later
import base64
import textwrap
import uuid

from dataclasses import dataclass
from io import BytesIO
from typing import Any
from urllib.parse import quote as html_quote

import pyotp
import qrcode
import django_rq

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token as ABSToken


class User(AbstractUser):
    @property
    def allow_api_usage(self):
        api_permissions = getattr(settings, 'API_PERMISSIONS', ())
        for permission in api_permissions:
            if self.has_perm(permission):
                return True
        return False


@dataclass
class EmailUpdate:
    user: User
    email: str


class Token(ABSToken):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(_("Key"), max_length=40, db_index=True, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='auth_tokens',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    comment = models.TextField(max_length=256)


class SecurityToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    secret = models.CharField(max_length=32, default=pyotp.random_base32)
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    enabled = models.BooleanField(_("Enabled"), default=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def create_recovery_codes(self, number=10):
        if not self.pk:
            raise RuntimeError('Cannot create recovery codes for unsaved security token')

        if self.recoverycode_set.count() == number:
            return

        for i in range(0, number):
            RecoveryCode(token=self).save()

    def recovery_codes_download(self):
        text = ''
        for code in self.recoverycode_set.all():
            text = text + f'{code.get_code_display()}\n'
        return html_quote(text)

    def uri(self):
        totp = pyotp.totp.TOTP(self.secret)
        return totp.provisioning_uri(
            name=self.user.get_username(),
            issuer_name=settings.TWOFA_DISPLAY_NAME)

    def validate(self, token, recovery_allowed=True):
        cache_key = f'user:totp:spend:{self.user.get_username()}'
        r_conn = django_rq.get_connection('default')

        if r_conn.sismember(cache_key, token):
            return False

        r_conn.sadd(cache_key, token)
        r_conn.expire(cache_key, 90, gt=True)

        if recovery_allowed:
            count, _ = self.recoverycode_set.filter(code=token.strip().replace(' ', '')).delete()
            if count:
                return True

        totp = pyotp.totp.TOTP(self.secret)
        return totp.verify(token)

    def qrcode(self):
        buf = BytesIO()
        img = qrcode.make(self.uri())
        img.save(buf)
        s = base64.b64encode(buf.getvalue())
        return s.decode('ascii')

    def get_secret_display(self):
        return ' '.join(textwrap.wrap(self.secret, 4))

    def __unicode__(self):
        return self.user.get_username()

    def __str__(self):
        return self.user.get_username()


def generate_recovery_key():
    return pyotp.random_base32()[:16]


class RecoveryCode(models.Model):
    token = models.ForeignKey(SecurityToken, on_delete=models.CASCADE)
    code = models.CharField(max_length=16, null=False, blank=False, default=generate_recovery_key)

    def get_code_display(self):
        return ' '.join(textwrap.wrap(self.code, 4))

    def __unicode__(self):
        return self.token.user
