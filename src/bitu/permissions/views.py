from typing import Any

from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse, Http404
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView

from .forms import PermissionRequestForm
from .models import PermissionRequest
from .permission import PermissionSet


class MyPermissionView(TemplateView):
    template_name = "permissions/permissions_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        p = PermissionSet()
        context = super().get_context_data(**kwargs)
        context['permissions'] = sorted(
            p.available_permissions(self.request.user), key=lambda x: x.name.__str__().lower())
        context['my_permissions'] = sorted(
            p.existing_permissions(self.request.user), key=lambda x: x.name.__str__().lower())
        return context


class PermissionRequestView(CreateView):
    form_class = PermissionRequestForm
    model = PermissionRequest
    success_url = reverse_lazy('permissions:list')

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.user = self.request.user
        form.instance.key = self.kwargs['key']
        form.instance.system = self.kwargs['system']
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        p = PermissionSet()
        context = super().get_context_data(**kwargs)
        context['permission'] = p.get_permission(self.kwargs['system'], self.kwargs['key'])
        return context


class PermissionRequestDetails(DetailView):
    model = PermissionRequest

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Check that the current user have access to the PermissionRequest object and raise
        # a 404 in case of ownership mismatch.
        try:
            self.request.user.permission_requests.get(pk=kwargs['pk'])
        except PermissionRequest.DoesNotExist:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
