import logging
import re

from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError


logger = logging.getLogger('bitu')


def UsernameValidator(username):
    from .models import BlockListUsername
    for blocklist in BlockListUsername.objects.all():
        m = re.search(blocklist.regex, username)
        if m:
            logger.info('username blocked; blocklist id: %s, regex: %s' % (blocklist.id, blocklist.regex))
            raise ValidationError(
            _("Invalid username, blocked"))
