from typing import Any

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.base import View

from .forms import SSHKeyCreateForm, SSHKeyActivateFormSingle
from .helpers import ssh_key_string_to_object, key_type_from_str
from .models import SSHKey
from .helpers import load_ssh_key


class SSHKeyAccessRestrict(View):
    """Permission check mixin for views displaying of modifying SSH keys.

    Args:
        View (django.views.generic.base.View): django base view
    """

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        try:
            # Fetch object as normal, but add the user to the query.
            SSHKey.objects.get(pk=pk, user=request.user)
            return super().dispatch(request, *args, **kwargs)
        except SSHKey.DoesNotExist:
            raise PermissionDenied()


class SSHKeyListView(ListView):
    model = SSHKey

    def get_queryset(self):
        load_ssh_key(self.request.user)
        return SSHKey.objects.filter(user=self.request.user).order_by('-active', 'ssh_public_key')


class SSHKeyCreateView(CreateView):
    model = SSHKey
    form_class = SSHKeyCreateForm
    success_url = reverse_lazy('keymanagement:list')

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        initial['system'] = self.request.GET.get('system')
        return initial

    def form_valid(self, form):
        key_object = ssh_key_string_to_object(form.instance.ssh_public_key)
        form.instance.user = self.request.user
        form.instance.ssh_public_key = form.instance.ssh_public_key.strip()
        form.instance.key_type = key_type_from_str(form.instance.ssh_public_key)
        form.instance.key_size = key_object.get_bits()

        if form.instance.system:
            form.instance.active = True

        # Check that we're doing a redirect, to the success URI, before adding
        # the success message.
        valid = super().form_valid(form)
        if valid.status_code == 302:
            messages.add_message(self.request, messages.SUCCESS, _('SSH key successfully uploaded.'))
        return valid


class SSHKeyDeleteView(DeleteView, SSHKeyAccessRestrict):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')

    def delete(self, request, *args, **kwargs):
        messages.add_message(request, messages.INFO, _('SSH key successfully deleted.'))
        return super().delete(request, *args, **kwargs)


class SSHKeyActivateView(UpdateView, SSHKeyAccessRestrict):
    model = SSHKey
    form_class = SSHKeyActivateFormSingle
    success_url = reverse_lazy('keymanagement:list')
    template_name = 'keymanagement/sshkey_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['systems'] = SSHKey.systems
        return context

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'].active = True
        return kw

    def form_valid(self, form):
        valid = super().form_valid(form)

        # Check that we're doing a redirect, to the success URI, before adding
        # the success message.
        if valid.status_code == 302:
            messages.add_message(self.request, messages.SUCCESS, _('SSH key has been activated.'))
        return valid


class SSHKeyDeactiveView(UpdateView, SSHKeyAccessRestrict):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')
    template_name = 'keymanagement/sshkey_deactivate.html'
    fields = []

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'].active = False
        return kw

    def form_valid(self, form):
        messages.add_message(self.request, messages.INFO, _('SSH key deactivated.'))
        return super().form_valid(form)
