# SPDX-License-Identifier: GPL-3.0-or-later
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from .views import (BlockEventLog,
                    BlockUserView,
                    BlockUserSearch,
                    ForgotUsernameView,
                    RequestPasswordResetView,
                    PasswordResetView,
                    UnBlockUserView,
                    PublicBlockEventLog)


app_name = 'wikimedia'
login_template = "oidc_login.html"
if hasattr(settings, "LOGIN_TEMPLATE"):
    login_template = settings.LOGIN_TEMPLATE

urlpatterns = [
    path('login/', TemplateView.as_view(template_name=login_template), name="login"),
    path("password/<uidb64>/<token>/", PasswordResetView.as_view(), name="reset"),
    path('password/wait/', TemplateView.as_view(template_name="request_password_wait.html"), name="password_wait"),
    path('password/', RequestPasswordResetView.as_view(), name="password_reset"),
    path('whoami/', ForgotUsernameView.as_view(), name="forgot_username"),
    path('block/', login_required(BlockUserSearch.as_view()), name="block_search"),
    path('block/<str:username>/log', login_required(BlockEventLog.as_view()), name="block_eventlog"),
    path('block/<str:username>', login_required(BlockUserView.as_view()), name="block_user"),
    path('unblock/<str:username>', login_required(UnBlockUserView.as_view()), name="unblock_user"),
    path('log/', PublicBlockEventLog.as_view(), name="public_block_log")
]
