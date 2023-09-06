from .forms import LDAPUserForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from .models import load_attribute_values, get_ldap_attributes_view

class LDAPUserFormView(FormView):
    template_name = 'properties.html'
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
