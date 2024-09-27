from django.contrib.auth.decorators import login_required
from django.urls import path


from .views import LDAPUserFormView, PasswordChangeView

app_name = 'ldapbackend'

urlpatterns = [
    path('properties/', login_required(LDAPUserFormView.as_view()), name='properties'),
    path('password/', login_required(PasswordChangeView.as_view()), name='change_password'),
]
