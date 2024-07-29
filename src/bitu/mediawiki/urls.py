# SPDX-License-Identifier: GPL-3.0-or-later
from django.conf import settings
from django.urls import path

from .api import UserTokenValidatorApiView


app_name = 'mediawiki'
urlpatterns = [path('api/totp/', UserTokenValidatorApiView.as_view()),]

if getattr(settings, 'ENABLE_API', False) and getattr(settings, 'MEDIAWIKI', False):
    urlpatterns.extend([
        path('api/totp/', UserTokenValidatorApiView.as_view()),
    ])
