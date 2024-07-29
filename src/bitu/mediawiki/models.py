import logging

import bituldap

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import TOTPValidator
from accounts.models import SecurityToken

User = get_user_model()

logger = logging.getLogger('bitu')


class UserTokenValidation(models.Model):
    username = models.CharField(_("username"), max_length=150)
    token = models.CharField(_("2FA Token"), max_length=32)
    sul = models.CharField(_("Single Unified Login"), max_length=150)
    valid = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        tokens = SecurityToken.objects.filter(user__username=self.username)
        for token in tokens:
            self.valid = token.validate(self.token)
            if self.valid:
                self.enabled = True
                break
        else:
            self.valid = False
            self.enabled = False

        ldap_user = bituldap.get_user(self.username)
        if ldap_user and 'wikimediaGlobalAccountName' in ldap_user:
            self.sul = ldap_user['wikimediaGlobalAccountName'].value

    class Meta:
        managed = False
