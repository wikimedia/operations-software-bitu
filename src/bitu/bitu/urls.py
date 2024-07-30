# SPDX-License-Identifier: GPL-3.0-or-later

"""bitu URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.auth.decorators import login_required


# Add view for favicon.ico, to avoid log spam.
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('favicon.ico', favicon_view),
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),
    path('rq/', include('django_rq.urls')),
    path('', include('social_django.urls', namespace='social')),
    path('accounts/', include('accounts.urls')),
    path('wikimedia/', include('wikimedia.urls')),
    path('ldapbackend/', include('ldapbackend.urls')),
    path('keymanagement/', include('keymanagement.urls')),
    path('about/', TemplateView.as_view(template_name="about.html"), name="about"),
    path('', login_required(RedirectView.as_view(pattern_name=settings.LOGIN_REDIRECT_URL),), name='overview'),
    path('403/', TemplateView.as_view(template_name='403.html')),
    path('500/', TemplateView.as_view(template_name='500.html')),
]

# Allow users to disable the signup form, if Bitu is only to be used for
# account management and not account creation.
if getattr(settings, 'ENABLE_SIGNUP', True):
    urlpatterns.append(
        path('signup/', include('signups.urls')),
    )

if hasattr(settings, 'ACCESS_REQUEST_RULES') and settings.ACCESS_REQUEST_RULES:
    urlpatterns.append(
        path('permissions/', include('permissions.urls')),
    )

# When developing, allow the built in Django webserver to serve static
# content. In production this is the job of the actual webserver.
if settings.DEBUG:
    urlpatterns + static(settings.STATIC_URL,
                         document_root=settings.STATIC_ROOT)
