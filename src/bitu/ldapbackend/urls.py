from django.contrib.auth.decorators import login_required
from django.urls import path


from .views import LDAPUserFormView

app_name = 'ldapbackend'

urlpatterns = [
    path('properties/', login_required(LDAPUserFormView.as_view()), name='properties'),
]
