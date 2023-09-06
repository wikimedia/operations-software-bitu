# SPDX-License-Identifier: GPL-3.0-or-later
from django.urls import path
from django.views.generic import TemplateView

from .views import SignupActivationFormView, SignupFormView

app_name = 'signups'
urlpatterns = [
    path("activate/<uidb64>/<token>/", SignupActivationFormView.as_view(), name="activate"),
    path('', SignupFormView.as_view(), name='signup'),
    path('success/', TemplateView.as_view(template_name="signups_success.html"), name="success"),
    path('thanks/', TemplateView.as_view(template_name="signups_thanks.html"), name="thanks"),
]
