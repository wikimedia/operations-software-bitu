from typing import Any

from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.base import View

from .forms import SSHKeyCreateForm, SSHKeyActivateFormSingle
from .helpers import ssh_key_string_to_object
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
        return SSHKey.objects.filter(user=self.request.user).order_by('-active')


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
        form.instance.key_type = key_object.get_name()
        form.instance.key_size = key_object.get_bits()

        if form.instance.system:
            form.instance.active = True

        return super().form_valid(form)


class SSHKeyDeleteView(DeleteView, SSHKeyAccessRestrict):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')


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


class SSHKeyDeactiveView(UpdateView, SSHKeyAccessRestrict):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')
    template_name = 'keymanagement/sshkey_deactivate.html'
    fields = []

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'].active = False
        return kw
