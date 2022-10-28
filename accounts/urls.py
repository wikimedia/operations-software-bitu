# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

app_name = 'accounts'
urlpatterns = [
    path('overview', login_required(TemplateView.as_view(template_name="overview.html")), name='overview')
]
