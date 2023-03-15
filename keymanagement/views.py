from django import forms
from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .helpers import ssh_key_string_to_object
from .models import SSHKey
#from .forms import SSHKeyAssignmentForm


class SSHKeyListView(ListView):
    model = SSHKey

    def get_queryset(self):
        return SSHKey.objects.filter(user=self.request.user).order_by('-active')


class SSHKeyCreateView(CreateView):
    model = SSHKey
    fields = ('ssh_public_key',)
    success_url = reverse_lazy('keymanagement:list')

    def form_valid(self, form):
        key_object = ssh_key_string_to_object(form.instance.ssh_public_key)
        form.instance.user = self.request.user
        form.instance.key_type = key_object.get_name()
        form.instance.key_size = key_object.get_bits()
        return super().form_valid(form)


class SSHKeyDeleteView(DeleteView):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')


class SSHKeyActivateView(UpdateView):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')
    fields = ('system',)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'].active = True
        return kw

    def form_valid(self, form):
        reponse = super().form_valid(form)

        # Deactivate any other keys assigned to the same system.
        # Backends will be updated in the background.
        instance = form.instance
        form.instance.user.ssh_keys.filter(system=instance.system).exclude(pk=instance.pk).update(active=False)
        return reponse

class SSHKeyDeactiveView(UpdateView):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')
    template_name = 'keymanagement/sshkey_deactivate.html'
    fields = []

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'].active = False
        return kw