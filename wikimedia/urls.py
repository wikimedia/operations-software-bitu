# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView


app_name = 'wikimedia'
urlpatterns = [
    path('login/', TemplateView.as_view(template_name="oidc_login.html"), name="login")
]
