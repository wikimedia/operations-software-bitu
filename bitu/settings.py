# SPDX-License-Identifier: GPL-3.0-or-later
"""
Development settings. We keep development settings in the settings.py
file, to make it easier for people to pick up the project and get going.

This file should only contain settings specific to the development
environent. Settings that are expected to work in both production,development,
and any other environments should go into base_settings.py.
"""
import ldap

from django_auth_ldap.config import LDAPSearch,GroupOfNamesType
from django.urls import reverse_lazy
from ldap3 import HASHED_SALTED_SHA


from .base_settings import *  # noqa

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-kcwxu%sx251dqdnyjn_cb(t3n=ud_v^o)#px9wy=g3=94)@zrz'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3', # noqa
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATICFILES_DIRS = [
    BASE_DIR / "static", # noqa
]

RQ_QUEUES = {
    'default': {
        'HOST': 'redis.local.wmftest.net',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },
    'notification': {
        'HOST': 'redis.local.wmftest.net',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },
}

BITU_LDAP = {
    'uri': 'ldap://openldap.local.wmftest.net:1389',
    'username': 'cn=admin,dc=example,dc=org',
    'password': 'adminpassword',
    'readonly': False,
    'connection_timeout': 5,
    'users': {
        'dn': 'ou=people,dc=example,dc=org',
        'object_classes': ['inetOrgPerson'],
        'auxiliary_classes': ['posixAccount', 'wikimediaPerson', 'ldapPublicKey'],
    }
}

LDAP_USER_CONF = {
    'default_gid': 2000,
}

BITU_SUB_SYSTEMS = {
    'ldapbackend': {
        'manage_ssh_keys': True,
        'ssh_keys_display_name': 'Wikimedia Cloud Service SSH keys',
        'default_gid': 2000,
        'password_hash': 'ldapbackend.helpers.hash_password',
        'password_hash_method': HASHED_SALTED_SHA,
        'default_groups': ['staff',],
        'attributes': {
            'edit': [{'name': 'sn', 'display': 'Firstname'},
                     {'name': 'givenName', 'display': 'Lastname'},
                     {'name': 'loginShell', 'display': 'Shell', 'choices':(
                        ('/bin/sh', '/bin/sh'),
                        ('/bin/bash', '/bin/bash'),
                        ('/usr/bin/tmux', '/usr/bin/tmux')),
                      'validators': ['ldapbackend.validators.login_shell_validator',]
                     },
                     {'name': 'fumble','display': 'invalid attribute'}
                     ],
            'view': [{'name': 'mail', 'display': 'e-mail',},
                      {'name': 'wikimediaGlobalAccountName', 'display': 'Wikimedia Global Account (SUL)',
                       'action': reverse_lazy('social:begin', args=['mediawiki']), 'action_label': 'refresh ↺'},
                      {'name': 'uidNumber', 'display': 'POSIX User ID'},
                      {'name': 'gidNumber', 'display': 'POSIX Group ID'},
                    ]
        },
        'default_groups': ['staff',]
    },
    'puppet': {
        'manage_ssh_keys': True,
    }
}

BITU_SSH_KEY_VALIDATOR = {
    'allowed_key_type': {
        'ssh-rsa': {'min_key_size': 2048},
        'ssh-ecdsa': {},
        'ssh-ed25519': {}
    }
}

AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "social_core.backends.mediawiki.MediaWiki",
    "django.contrib.auth.backends.ModelBackend",
]


AUTH_LDAP_BIND_DN = "cn=admin,dc=example,dc=org"
AUTH_LDAP_BIND_PASSWORD = "adminpassword"
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")
AUTH_LDAP_SERVER_URI = "ldap://openldap.local.wmftest.net:1389"
AUTH_LDAP_FIND_GROUP_PERMS = True

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=people,dc=example,dc=org", ldap.SCOPE_SUBTREE, "(uid=%(user)s)"
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "dc=example,dc=org",
     ldap.SCOPE_SUBTREE, "(objectClass=groupOfNames)",
)

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": "cn=staff,ou=groups,dc=example,dc=org",
    "is_staff": "cn=staff,ou=groups,dc=example,dc=org",
    "is_superuser": "cn=sudoers,ou=groups,dc=example,dc=org",
}


SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

# Byparse most pipelines to avoid issues with groups and
# prevent logging in with MediaWiki account.
SOCIAL_AUTH_MEDIAWIKI_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'wikimedia.social_pipeline.global_account_link',)

SOCIAL_AUTH_MEDIAWIKI_URL = 'https://meta.wikimedia.org/w/index.php'
SOCIAL_AUTH_MEDIAWIKI_CALLBACK = 'http://localhost:8000/complete/mediawiki'
LOGOUT_REDIRECT_URL = 'wikimedia:login'
LOGIN_URL = LOGOUT_REDIRECT_URL
CAPTCHA_LENGTH = 5
PASSWORD_RESET_TIMEOUT = 60 * 3 # Three minutes, rather low, but for testing.
BITU_DOMAIN = 'http://localhost:8000'

# For testing purposes only. In production use a real SMTP server.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
BITU_NOTIFICATION = {
    'default_sender': 'noc@example.org',
    'signup_template_prefix': 'email_wmf_signup_activation',
    'signup_subject': 'Wikimedia Developer Account activation'
}

SIGNUP_USERNAME_VALIDATORS = ['ldapbackend.validators.LDAPUsernameValidator',
                              'ldapbackend.validators.unix_username_validator',
                              'signups.validators.UsernameValidator'
                              ]

SIGNUP_INFO_TEMPLATE = 'signup_info_wmf.html'