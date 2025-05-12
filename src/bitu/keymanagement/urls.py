# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView


from .views import (SSHKeyActivateView,
                    SSHKeyCreateView,
                    SSHKeyDeactiveView,
                    SSHKeyDeleteView,
                    SSHKeyListView,
                    )

app_name = 'keymanagement'
urlpatterns = [
    path('create/', login_required(SSHKeyCreateView.as_view()), name='create'),
    path('delete/<int:pk>/', login_required(SSHKeyDeleteView.as_view()), name='delete'),
    path('activate/<int:pk>/', login_required(SSHKeyActivateView.as_view()), name='activate'),
    path('deactivate/<int:pk>/', login_required(SSHKeyDeactiveView.as_view()), name='deactivate'),
    path('', login_required(SSHKeyListView.as_view()), name='list'),
    path('list/', login_required(TemplateView.as_view(template_name="keymanagement/sshkey_app.html")), name="list_keys")
]
