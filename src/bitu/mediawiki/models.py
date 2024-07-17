import logging

import bituldap

from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import TOTPValidator


logger = logging.getLogger('bitu')


class UserTokenValidation(models.Model):
    username = models.CharField(_("username"), max_length=150)
    token = models.CharField(_("2FA Token"), max_length=32)
    sul = models.CharField(_("Single Unified Login"), max_length=150)
    valid = models.BooleanField(default=False)
    enabled = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        ldap_user = bituldap.get_user(self.username)
        if ldap_user and 'wikimediaGlobalAccountName' in ldap_user:
            self.sul = ldap_user['wikimediaGlobalAccountName'].value
            try:
                self.enabled, self.valid = TOTPValidator(self.sul, self.token)
            except Exception as e:
                logger.warning(f'failed to get call MediaWiki OATH, exception: {e}')
                self.enabled = self.valid = False

    class Meta:
        managed = False
