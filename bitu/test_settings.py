"""
Minimum required settings for running tests.
"""

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
    'social_django',
    'accounts',
    'captcha',
    'signups',
    'ldapbackend.apps.LdapConfig',
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
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },
    'notification': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
    },
}

BITU_SUB_SYSTEMS = {
    'ldapbackend': {
        'manage_ssh_keys': False,
        'default_gid': 2000,
        'password_hash': 'ldapbackend.helpers.hash_password',
        'password_hash_method': HASHED_SALTED_SHA,
    }
}