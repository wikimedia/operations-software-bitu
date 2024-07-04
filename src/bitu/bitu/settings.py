# SPDX-License-Identifier: GPL-3.0-or-later
"""
Development settings. We keep development settings in the settings.py
file, to make it easier for people to pick up the project and get going.

This file should only contain settings specific to the development
environent. Settings that are expected to work in both production,development,
and any other environments should go into base_settings.py.
"""
import ldap

from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
from django.urls import reverse_lazy
from ldap3 import HASHED_SALTED_SHA


from .base_settings import *  # noqa

# Allow developers to define local variables in
# .local_settings.py for debugging and testing
# purposes.
try:
    from .local_settings import *  # noqa
except ImportError:
    pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-kcwxu%sx251dqdnyjn_cb(t3n=ud_v^o)#px9wy=g3=94)@zrz'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'idm',
        'HOST': 'db.local.wmftest.net',
        'PORT': 3307,
        'USER': 'idm',
        'PASSWORD': 'secret',
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "bitu": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
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
    'uri': 'ldap://openldap.local.wmftest.net:2389',
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

USER_AGENT = 'Bitu Identity Manager/0.1 (contact@example.org)'

LDAP_USER_CONF = {
    'default_gid': 2000,
}

BITU_SUB_SYSTEMS = {
    'ldapbackend': {
        'manage_ssh_keys': True,
        'ssh_keys_display_name': 'Wikimedia Cloud Services',
        'default_gid': 2000,
        'password_hash': 'ldapbackend.helpers.hash_password',
        'password_hash_method': HASHED_SALTED_SHA,
        'default_groups': ['staff',],
        # Validate that the UID returned by the LDAP library is within one of the
        # following allowed ranges. If not account creation will fail.
        # set to [] or remove key to disable this check.
        'uid_ranges': [{'min': 1000, 'max': 20000}, {'min': 1000000, 'max': 1999999}],
        'attributes': {
            'edit': [{'name': 'sn', 'display': 'Firstname'},
                     {'name': 'givenName', 'display': 'Lastname'},
                     {'name': 'loginShell', 'display': 'Shell', 'choices': (
                        ('/bin/sh', '/bin/sh'),
                        ('/bin/bash', '/bin/bash'),
                        ('/usr/bin/tmux', '/usr/bin/tmux')),
                      'validators': ['ldapbackend.validators.login_shell_validator',]
                     },
                     {'name': 'fumble','display': 'invalid attribute'}
                     ],
            'view': [{'name': 'mail', 'display': 'e-mail', 'action': reverse_lazy('accounts:email'), 'action_label': 'Update',},
                      {'name': 'wikimediaGlobalAccountName', 'display': 'Wikimedia Global Account (SUL)', 'tooltip': 'This is the account you use when signing into one of our wikis, including Wikipedia.',
                       'action': reverse_lazy('social:begin', args=['mediawiki']), 'action_label': 'refresh ↺', 'action_label2': 'Link account'},
                      {'name': 'uidNumber', 'display': 'POSIX User ID', 'tooltip': 'If you have SSH access to Cloud VPS, Toolforge or other Wikimedia servers, this will be the ID they use to identify you.'},
                      {'name': 'gidNumber', 'display': 'POSIX Group ID', 'tooltip': 'If you have SSH access to Cloud VPS, Toolforge or other Wikimedia servers, this will be the ID of your primary user group.'},
                    ]
        },
    },
    'puppet': {
        'manage_ssh_keys': False,
    }
}

BITU_SSH_KEY_VALIDATOR = {
    'allowed_key_type': {
        'ssh-rsa': {'min_key_size': 2048},
        'ssh-ecdsa': {},
        'ssh-ed25519': {},
        'sk-ssh-ed25519@openssh.com': {}
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
AUTH_LDAP_SERVER_URI = "ldap://openldap.local.wmftest.net:2389"
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

# Uncomment the lines below to test wikimedia IDP integration, leave commented
# in developer environment to use LDAP backend directly.
# LOGOUT_REDIRECT_URL = 'wikimedia:login'
# LOGIN_URL = LOGOUT_REDIRECT_URL
CAPTCHA_CHALLENGE_FUNCT = 'signups.forms.captcha_input_generator'
CAPTCHA_IMAGE_SIZE = (130,40)
CAPTCHA_FONT_SIZE = 28
PASSWORD_RESET_TIMEOUT = 60 * 3  # Three minutes, rather low, but for testing.
BITU_DOMAIN = 'http://localhost:8000'

# For testing purposes only. In production use a real SMTP server.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
BITU_NOTIFICATION = {
    'default_sender': 'noc@example.org',
    'signup_template_prefix': 'email_wmf_signup_activation',
    'signup_subject': 'Wikimedia Developer Account activation'
}

SIGNUP_USERNAME_VALIDATORS = ['ldapbackend.validators.LDAPUsernameValidator',
                              'signups.validators.UsernameValidator',
                              'signups.validators.IsURLValidator'
                              ]

SIGNUP_UID_VALIDATORS = ['ldapbackend.validators.unix_username_regex_validator',
                         'ldapbackend.validators.unix_username_length_validator',
                         'signups.validators.UsernameValidator']

SIGNUP_EMAIL_VALIDATORS = ['ldapbackend.validators.LDAPEmailValidator',]

SIGNUP_INFO_TEMPLATE = 'signup_info_wmf.html'
LOGIN_REDIRECT_URL = 'ldapbackend:properties'

ADMINS_LIMITED = []
ENABLE_API = True

API_PERMISSIONS = (
    'signups.add_uservalidation',
    'signups.view_blocklistip'
)



if DEBUG:
    for queueConfig in RQ_QUEUES.values():
        queueConfig['ASYNC'] = False
