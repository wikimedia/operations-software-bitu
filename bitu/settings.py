# SPDX-License-Identifier: GPL-3.0-or-later
"""
Development settings. We keep development settings in the settings.py
file, to make it easier for people to pick up the project and get going.

This file should only contain settings specific to the development
environent. Settings that are expected to work in both production,development,
and any other environments should go into base_settings.py.
"""

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
}