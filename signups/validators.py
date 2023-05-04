import re

from django.utils.translation import gettext_lazy as _
from django.forms import ValidationError


def UsernameValidator(username):
    from .models import BlockListUsername
    for blocklist in BlockListUsername.objects.all():
        m = re.search(blocklist.regex, username)
        if m:
            raise ValidationError(
            _("Invalid username, blocked"))
