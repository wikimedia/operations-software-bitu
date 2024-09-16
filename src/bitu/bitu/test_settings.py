# SPDX-License-Identifier: GPL-3.0-or-later
"""
Minimum required settings for running tests.
"""

import django_rq

from ldap3 import HASHED_SALTED_SHA

from .base_settings import *  # noqa

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
    'permissions.apps.PermissionsConfig',
    'wikimedia.apps.WikimediaConfig',
    'keymanagement.apps.KeymanagementConfig'
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'TESTING'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TESTING = True
ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test'
    }
}

RQ_QUEUES = {
    'default': {
        'URL': 'redis://localhost:6380/0',
        'ASYNC': False
    },

    'notification': {
        'URL': 'redis://localhost:6380/0',
        'ASYNC': False
    },
}


# Before django_rq has the chance to do ANYTHING, hack in a fake connection function.
# Doing this at any later point will result in django_rq already having loaded parts
# of the regular Redis connection handling, completely bypassing FakeRedis
def get_fake_connection(config, strict):
    from fakeredis import FakeRedis, FakeStrictRedis
    redis_cls = FakeStrictRedis if strict else FakeRedis
    if "URL" in config:
        return redis_cls.from_url(
            config["URL"],
            db=config.get("DB"),
        )

    return redis_cls(
        host=config["HOST"],
        port=config["PORT"],
        db=config.get("DB", 0),
        username=config.get("USERNAME", None),
        password=config.get("PASSWORD"),
    )


django_rq.queues.get_redis_connection = get_fake_connection

LDAP_USER_CONF = {
    'default_gid': 2000
}

BITU_DOMAIN = 'https://localhost'
BITU_NOTIFICATION = {
    'default_sender': 'no-reply@example.org'
}
BITU_SUB_SYSTEMS = {
    'ldapbackend': {
        'permissions': 'ldapbackend.permission.LDAPPermissions',
        'manage_ssh_keys': True,
        'ssh_keys_display_name': 'LDAP',
        'default_gid': 2000,
        'password_hash': 'ldapbackend.helpers.hash_password',
        'password_hash_method': HASHED_SALTED_SHA,
    }
}

# Ideally we'd like to load these in the test cases, but due to test sequence in which
# modules are loaded, that will cause the models to load without validators.
SIGNUP_USERNAME_VALIDATORS = ['ldapbackend.validators.LDAPUsernameValidator',
                              'signups.validators.UsernameValidator',
                              'signups.validators.IsURLValidator'
                              ]

ENABLE_API = True
ENABLE_2FA = True

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_DIRS = [
    BASE_DIR / "static", # noqa
]

ACCESS_REQUEST_RULES = {
    'ldapbackend': {
        'cn=nda,ou=groups,dc=example,dc=org': [{
            'module': 'permissions.validators.manager_approval',
            'managers': ['wwaller'],
            'count': 1
        }]
    }
}
