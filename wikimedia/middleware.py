from typing import Callable, TYPE_CHECKING

from .validators import wikimedia_global_account

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


if TYPE_CHECKING:
    User = get_user_model()


def global_account_valid_middleware(get_response: Callable):
    """Middleware for inject "please link accounts" message.

    To be used as a middleware for incoming requests. If the
    current user has not yet linked their IDM account with
    their Wikimedia global account (https://wikitech.wikimedia.org/wiki/Terminology)
    inject a prompt requesting that they do so, with a link.

    To enable this middleware function, add the module path to
    the MIDDLEWARE section in the Django settings file:

    .. code-block:: python

        MIDDLEWARE = [
            ...
            'wikimedia.middleware.global_account_valid_middleware',
        ]


    Args:
        get_response: Middleware callable

    """

    def middleware(request):
        # Check if we need to ask the user to link their account
        # to their Wikimedia Global Account (Wiki account).
        user: 'User' = request.user
        storage = messages.get_messages(request)

        # Check that we don't already have messages on the
        # 'queue'. This is to avoid duplicate messages for
        # this check.
        m = len(storage._loaded_messages)

        valid = wikimedia_global_account(request, user)

        if not valid and m == 0:
            messages.warning(request, mark_safe(
                _("""If you have a "Wikimedia global account" to edit the wikis, please connect it to your account <a href="%(action)s">here</a>.
                (you will be prompted for your wiki password). If you don't have a Wikimedia global account yet, you can create one
                 <a href="https://meta.wikimedia.org/w/index.php?title=Special:CreateAccount&returnto=Main+Page">here</a>.<br><br>
                 <strong>Note:</strong> if you have multiple Wiki accounts, e.g. a Wikimedia Foundation staff account in addition to your personal account, please ensure
                 that you are signed in with the correct account on <a href="https://meta.wikimedia.org">meta.wikimedia.org</a> before clicking approve.
                """
                % {'action': reverse('social:begin', args=['mediawiki'])})))

        return get_response(request)

    return middleware