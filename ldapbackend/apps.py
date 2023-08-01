# SPDX-License-Identifier: GPL-3.0-or-later
from django.apps import AppConfig
from django.conf import settings
from .signals import create_user, update_user
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save


class LdapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ldapbackend'

    def ready(self) -> None:
        if not hasattr(settings, 'LDAP_USER_CONF'):
            raise Exception()

        from signups.models import Signup
        User = get_user_model()

        post_save.connect(create_user, Signup)
        post_save.connect(update_user, User)
