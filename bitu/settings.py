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
        'auxiliary_classes': ['posixAccount'],
    }
}

LDAP_USER_CONF = {
    'default_gid': 2000,
}

BITU_SUB_SYSTEMS = {
    'ldapbackend': {
        'default_gid': 2000,
        'password_hash': 'ldapbackend.helpers.hash_password',
        'password_hash_method': HASHED_SALTED_SHA,
        'default_groups': ['staff',]
    }
}

AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
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