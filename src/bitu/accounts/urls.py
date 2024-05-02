# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView

from .views import (
    TokenCreateView,
    TokenDeleteView,
    TokensListView,
    UpdateEmailView,
    VerifyEmailView
)

app_name = 'accounts'
urlpatterns = [
    path('', login_required(TemplateView.as_view(template_name='overview.html')), name='overview'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('email/', login_required(UpdateEmailView.as_view()), name='email'),
    path('email/<uidb64>/<token>/', login_required(VerifyEmailView.as_view()), name='email_verify'),
    path('api/tokens/', login_required(TokensListView.as_view()), name='api_tokens'),
    path('api/tokens/create/', login_required(TokenCreateView.as_view()), name='api_token_create'),
    path('api/tokens/delete/<pk>', login_required(TokenDeleteView.as_view()), name='api_token_delete'),
]
