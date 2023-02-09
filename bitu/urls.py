# SPDX-License-Identifier: GPL-3.0-or-later

"""bitu URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView, TemplateView
from django.contrib.auth.decorators import login_required


# Add view for favicon.ico, to avoid log spam.
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('favicon.ico', favicon_view),
    path('admin/', admin.site.urls),
    path('rq/', include('django_rq.urls')),
    path('', include('social_django.urls', namespace='social')),
    path('signup/', include('signups.urls')),
    path('accounts/', include('accounts.urls')),
    path('wikimedia/', include('wikimedia.urls')),
    path('', login_required(TemplateView.as_view(template_name='overview.html')), name='overview'),
]

# When developing, allow the built in Django webserver to serve static
# content. In production this is the job of the actual webserver.
if settings.DEBUG:
    urlpatterns + static(settings.STATIC_URL,
                         document_root=settings.STATIC_ROOT)
