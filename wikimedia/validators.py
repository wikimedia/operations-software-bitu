from typing import Tuple
import bituldap


from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


User = get_user_model()


def wikimedia_global_account(request, user:'User') -> bool:
    # The user should be authenticated at this point
    # but let's check. If anonymous, lie and say that
    # the user isn't required to link the accounts.
    if user.is_anonymous:
        return True

    # Use session storage to avoid querying LDAP more
    # than we need to.
    if request.session.get('wikimedia_global', False):
        return True

    ldap_user = bituldap.get_user(user.get_username())
    if not ldap_user:
        return True

    if not ldap_user.wikimediaGlobalAccountId:
        return False

    # User has already linked their accounts.
    request.session['wikimedia_global'] = True
    return True