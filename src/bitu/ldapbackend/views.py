import logging

from typing import Any

from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from .forms import LDAPUserForm, PasswordChangeForm
from .helpers import change_password
from .models import load_attribute_values, get_ldap_attributes_view


logger = logging.getLogger('bitu')


class LDAPUserFormView(FormView):
    template_name = 'ldapbackend/properties.html'
    form_class = LDAPUserForm
    success_url = reverse_lazy('ldapbackend:properties')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        read_only = get_ldap_attributes_view()
        context = super().get_context_data(**kwargs)
        context['ro_attrs'] = load_attribute_values(self.request.user, read_only)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['uid'] = self.request.user.username
        return kwargs

    def form_valid(self, form: LDAPUserForm):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        if form.is_valid():
            form.save()
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _('Properties updated'))
        return super().form_valid(form)


class PasswordChangeView(FormView):
    template_name = 'ldapbackend/password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('ldapbackend:change_password')


    def get_initial(self) -> dict[str, Any]:
        data = super().get_initial()
        data['username'] = self.request.user.get_username()
        return data

    def form_valid(self, form: PasswordChangeForm) -> HttpResponse:
        success = change_password(self.request.user, form.cleaned_data['password1'])
        if success:
            logger.info(f'password changed for user: {self.request.user.get_username()}')
            messages.add_message(self.request, level=messages.SUCCESS, message=_('Password successfully changed'), )
        else:
            logger.warning(f'password change failed for user: {self.request.user.get_username()}')
            messages.add_message(self.request, level=messages.ERROR, message=_('Failed to update password'), )
        return super().form_valid(form)