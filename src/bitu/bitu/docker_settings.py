# SPDX-License-Identifier: GPL-3.0-or-later
"""
Minimum required settings for running tests.
"""

import os

import ldap

from django.urls import reverse_lazy
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
from ldap3 import HASHED_SALTED_SHA

from bitu.base_settings import *  # noqa

allowed_hosts = os.environ['ALLOWED_HOSTS'].split(',') if 'ALLOWED_HOSTS' in os.environ else ['*']
redis_rq_host = os.environ['RQ_REDIS_HOST']
redis_rq_port = os.environ['RQ_REDIS_PORT'] if 'RQ_REDIS_PORT' in os.environ else '6379'
ldap_uri = os.environ['LDAP_SERVER_URI']
ldap_user_dn = os.environ['LDAP_USER_DN']
ldap_password = os.environ['LDAP_PASSWORD']
ldap_user_search_base = os.environ['LDAP_USER_SEARCH_BASE'] if 'LDAP_USER_SEARCH_BASE' in os.environ else 'ou=people,dc=example,dc=org'
ldap_user_search = os.environ['LDAP_USER_SEARCH_QUERY'] if 'LDAP_USER_SEARCH_QUERY' in os.environ else '(uid=%(user)s)'
ldap_group_search_base = os.environ['LDAP_BASE_DN'] if 'LDAP_BASE_DN' in os.environ else 'ou=groups,dc=example,dc=org'
ldap_aux_groups = os.environ['LDAP_AUX_GROUPS'].split(',') if 'LDAP_AUX_GROUPS' in os.environ else ['posixAccount', 'wikimediaPerson', 'ldapPublicKey']
ldap_user_active = os.environ['ACTIVE_GROUP_DN'] if 'ACTIVE_GROUP_DN' in os.environ else 'cn=staff,ou=groups,dc=example,dc=org'
ldap_user_staff = os.environ['STAFF_GROUP_DN'] if 'STAFF_GROUP_DN' in os.environ else 'cn=staff,ou=groups,dc=example,dc=org'
ldap_user_superuser = os.environ['SUPERUSER_GROUP_DN'] if 'SUPERUSER_GROUP_DN' in os.environ else 'cn=admin,ou=groups,dc=example,dc=org'
database_username = os.environ['DATABASE_USER']
database_password = os.environ['DATABASE_PASSWORD']
database_name = os.environ['DATABASE_NAME']
database_host = os.environ['DATABASE_HOST']
database_port = os.environ['DATABASE_PORT'] if 'DATABASE_PORT' in os.environ else '3306'
database_driver = os.environ['DATABASE_ENGINE'] if 'DATABASE_ENGINE' in os.environ else 'django.db.backends.sqlite3'

# Allow API usage.
ENABLE_API = os.environ['ENABLE_API'] if 'ENABLE_API' in os.environ else False

# 2FA Proxy / MediaWiki.
# Currently only used for the 2FA proxy, but may be reused for other MediaWiki integrations in the future.
# Access to MediaWiki functionality is limited to the permissions granted by the provided keys.
mediawiki_url = os.environ['MEDIAWIKI_URL'] if 'MEDIAWIKI_URL' in os.environ else None
mediawiki_consumer_token = os.environ['MEDIAWIKI_CONSUMER_TOKEN'] if 'MEDIAWIKI_CONSUMER_TOKEN' in os.environ else None
mediawiki_consumer_secret = os.environ['MEDIAWIKI_CONSUMER_SECRET'] if 'MEDIAWIKI_CONSUMER_SECRET' in os.environ else None
mediawiki_access_token = os.environ['MEDIAWIKI_ACCESS_TOKEN'] if 'MEDIAWIKI_ACCESS_TOKEN' in os.environ else None
mediawiki_access_secret = os.environ['MEDIAWIKI_ACCESS_SECRET'] if 'MEDIAWIKI_ACCESS_SECRET' in os.environ else None

if mediawiki_url:
    MEDIAWIKI = {
        'host': mediawiki_url,
        'consumer_token': mediawiki_consumer_token,
        'consumer_secret': mediawiki_consumer_secret,
        'access_token': mediawiki_access_token,
        'access_secret': mediawiki_access_secret
    }


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_rq',
    'rest_framework',
    'social_django',
    'accounts',
    'captcha',
    'signups',
    'ldapbackend.apps.LdapConfig',
    'wikimedia.apps.WikimediaConfig',
    'keymanagement.apps.KeymanagementConfig'
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getattr(os.environ, 'DJANGO_DEBUGGING', True)
TESTING = True
ALLOWED_HOSTS = allowed_hosts

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': database_driver,
        'NAME': database_name,
        'HOST': database_host,
        'PORT': database_port,
        'USER': database_username,
        'PASSWORD': database_password,
    }
}

print(DATABASES)

RQ_QUEUES = {
    'default': {
        'URL': f'redis://{redis_rq_host}:{redis_rq_port}/0',
        'ASYNC': False
    },

    'notification': {
        'URL': f'redis://{redis_rq_host}:{redis_rq_port}/0',
        'ASYNC': False
    },
}


LDAP_USER_CONF = {
    'default_gid': 2000
}

BITU_LDAP = {
    'uri': ldap_uri,
    'username': ldap_user_dn,
    'password': ldap_password,
    'readonly': False,
    'connection_timeout': 5,
    'users': {
        'dn': ldap_user_search_base,
        'object_classes': ['inetOrgPerson'],
        'auxiliary_classes': ldap_aux_groups,
    }
}

BITU_SUB_SYSTEMS = {
    'ldapbackend': {
        'manage_ssh_keys': True,
        'ssh_keys_display_name': 'LDAP',
        'default_gid': 2000,
        'password_hash': 'ldapbackend.helpers.hash_password',
        'password_hash_method': HASHED_SALTED_SHA,
        'attributes': {
            'edit': [{'name': 'sn', 'display': 'Firstname'},
                     {'name': 'givenName', 'display': 'Lastname'},
                     {'name': 'loginShell', 'display': 'Shell', 'choices': (
                        ('/bin/sh', '/bin/sh'),
                        ('/bin/bash', '/bin/bash'),
                        ('/usr/bin/tmux', '/usr/bin/tmux')),
                      'validators': ['ldapbackend.validators.login_shell_validator',]
                     },
                     ],
            'view': [{'name': 'mail', 'display': 'e-mail'},
                     {'name': 'uidNumber', 'display': 'POSIX User ID', 'tooltip': 'If you have SSH access to Cloud VPS, Toolforge or other Wikimedia servers, this will be the ID they use to identify you.'},
                     {'name': 'gidNumber', 'display': 'POSIX Group ID', 'tooltip': 'If you have SSH access to Cloud VPS, Toolforge or other Wikimedia servers, this will be the ID of your primary user group.'},
                    ]
        },
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
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django_auth_ldap": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_LDAP_BIND_DN = ldap_user_dn
AUTH_LDAP_BIND_PASSWORD = ldap_password
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")
AUTH_LDAP_SERVER_URI = ldap_uri
AUTH_LDAP_FIND_GROUP_PERMS = True

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    ldap_user_search_base, ldap.SCOPE_SUBTREE, ldap_user_search
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    ldap_group_search_base,
    ldap.SCOPE_SUBTREE, "(objectClass=groupOfNames)",
)

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": ldap_user_active,
    "is_staff": ldap_user_staff,
    "is_superuser": ldap_user_superuser,
}

# Ideally we'd like to load these in the test cases, but due to test sequence in which
# modules are loaded, that will cause the models to load without validators.
SIGNUP_USERNAME_VALIDATORS = ['ldapbackend.validators.LDAPUsernameValidator',
                              'signups.validators.UsernameValidator',
                              'signups.validators.IsURLValidator'
                              ]

LOGIN_REDIRECT_URL = 'ldapbackend:properties'
LOGOUT_REDIRECT_URL = '/'

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_DIRS = [
    BASE_DIR / "static", # noqa
]

# Disable async, to avoid having to spin up workers.
for queueConfig in RQ_QUEUES.values():
        queueConfig['ASYNC'] = False