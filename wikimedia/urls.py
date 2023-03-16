# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from .views import RequestPasswordResetView, PasswordResetView


app_name = 'wikimedia'
urlpatterns = [
    path('login/', TemplateView.as_view(template_name="oidc_login.html"), name="login"),
    path("password/<uidb64>/<token>/", PasswordResetView.as_view(), name="reset"),
    path('password/wait/', TemplateView.as_view(template_name="request_password_wait.html"), name="password_wait"),
    path('password/', RequestPasswordResetView.as_view(), name="password_reset")
]
