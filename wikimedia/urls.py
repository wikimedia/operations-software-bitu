# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import MediaWikiLinkView


app_name = 'wikimedia'
urlpatterns = []
