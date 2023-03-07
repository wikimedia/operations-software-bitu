from .validators import wikimedia_global_account

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


User = get_user_model()


def global_account_valid_middleware(get_response):

    def middleware(request):
        # Check if we need to ask the user to link their account
        # to their WikiMedia Global Account (Wiki account).
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
                 <a href="https://meta.wikimedia.org/w/index.php?title=Special:CreateAccount&returnto=Main+Page">here</a>.
                """
                % {'action': reverse('social:begin', args=['mediawiki'])})))

        return get_response(request)

    return middleware