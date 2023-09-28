from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import SSHKeyCreateForm, SSHKeyActivateFormSingle
from .helpers import ssh_key_string_to_object
from .models import SSHKey


class IsSuperUserViewMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin for limiting access to views to superusers."""

    def test_func(self):
        """Overwrites test function for UserPassesTestMixin.

        Returns:
            bool: User passes test (true/false)
        """
        return self.request.user.is_superuser


class SSHKeyListView(IsSuperUserViewMixin, ListView):
    model = SSHKey

    def get_queryset(self):
        return SSHKey.objects.filter(user=self.request.user).order_by('-active')


class SSHKeyCreateView(IsSuperUserViewMixin, CreateView):
    model = SSHKey
    form_class = SSHKeyCreateForm
    success_url = reverse_lazy('keymanagement:list')

    def form_valid(self, form):
        key_object = ssh_key_string_to_object(form.instance.ssh_public_key)
        form.instance.user = self.request.user
        form.instance.key_type = key_object.get_name()
        form.instance.key_size = key_object.get_bits()
        return super().form_valid(form)


class SSHKeyDeleteView(IsSuperUserViewMixin, DeleteView):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')


class SSHKeyActivateView(IsSuperUserViewMixin, UpdateView):
    model = SSHKey
    form_class = SSHKeyActivateFormSingle
    success_url = reverse_lazy('keymanagement:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['systems'] = SSHKey.systems
        return context

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'].active = True
        return kw


class SSHKeyDeactiveView(IsSuperUserViewMixin, UpdateView):
    model = SSHKey
    success_url = reverse_lazy('keymanagement:list')
    template_name = 'keymanagement/sshkey_deactivate.html'
    fields = []

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['instance'].active = False
        return kw