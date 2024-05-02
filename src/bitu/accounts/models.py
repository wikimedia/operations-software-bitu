# SPDX-License-Identifier: GPL-3.0-or-later
import uuid

from dataclasses import dataclass

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
