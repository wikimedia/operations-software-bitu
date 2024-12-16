import logging
import re

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger('bitu')


def UsernameValidator(username):
    from .models import BlockListUsername
    for blocklist in BlockListUsername.objects.all():
        m = re.search(blocklist.regex, username)
        if m:
            logger.info('username blocked; blocklist id: %s, regex: %s' % (blocklist.id, blocklist.regex))
            raise ValidationError(
            _("Invalid username, blocked"))


def IsURLValidator(username):
    validator = URLValidator()
    is_url = False
    try:
        validator(username)
        is_url = True
    except ValidationError:
        pass

    if is_url:
        logger.info(f'username blocked, URIs are not allowed, username: {username}')
        raise ValidationError(
            _("Invalid username, invalid format")
        )


def IsUsernameEmail(username):
    validator = EmailValidator()
    is_email = False
    try:
        validator(username)
        is_email = True
    except ValidationError:
        pass

    if is_email:
        logger.info(f'username blocked, email addresses are not allowed, username: {username}')
        raise ValidationError(
            _("Invalid username, invalid format (email)")
        )