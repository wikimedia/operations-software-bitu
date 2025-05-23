from typing import Any

from django.core.paginator import Paginator
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse, Http404
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from .forms import PermissionRequestForm
from .models import PermissionRequest, Log as PermissionLog
from .permission import permission_set


class MyPermissionView(TemplateView):
    template_name = "permissions/permissions_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['permissions'] = sorted(
            permission_set.available_permissions(self.request.user), key=lambda x: x.name.__str__().lower())
        context['my_permissions'] = sorted(
            permission_set.existing_permissions(self.request.user), key=lambda x: x.name.__str__().lower())
        context['logs'] = PermissionLog.objects.filter(request__user=self.request.user).order_by('-created')
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
        context = super().get_context_data(**kwargs)
        permission = permission_set.get_permission(self.kwargs['system'], self.kwargs['key'])
        available = permission_set.available_permissions(self.request.user)
        if not permission or permission not in available:
            raise Http404

        context['permission'] = permission
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


class PermissionRequestLogCreateView(CreateView):
    """Base view for approval and rejection.
    Approvals and rejections are identical in rules, except for
    the setting of the approval fields. Using a shared base view
    ensures that logic is not dublicated.

    Args:
        CreateView (CreateView): Generic Django CreateView
    """

    model = PermissionLog
    fields = ('comment',)
    success_url = reverse_lazy('permissions:pending')

    @property
    def permission_request(self):
        # No need to check return value, as objects.get will raise
        # PermissionRequest.DoesNotExist and trigger a 404 if pk is
        # invalid.
        return PermissionRequest.objects.get(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # Verify that we're allowed to approve or reject this requests by
        # checking if the PermissionRequest object if in the QuerySet of
        # requests we are expected to handle. Raise a Http404 otherwise, leaving
        # no indication of whether or not this object exists.
        try:
            permission_set.get_pending(self.request.user).get(pk=self.permission_request.pk)
        except PermissionRequest.DoesNotExist:
            raise Http404

        context = super().get_context_data(**kwargs)
        context['request'] = self.permission_request
        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.created_by = self.request.user
        form.instance.request = self.get_context_data()['request']
        return super().form_valid(form)


class PermissionRequestApprove(PermissionRequestLogCreateView):
    template_name = 'permissions/approve_form.html'

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        # Check for the name of the approve button in the form data.
        # The name will be in the form data, if the "Approve" button
        # was clicked, but not the "Reject" button.
        if "approve" in self.request.POST:
            form.instance.approved = True
        return super().form_valid(form)


class PermissionRequestList(ListView):
    model = PermissionRequest

    # Do not use "pagination" as this will paginate the model and not the logs.
    log_pagination = 25

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.permission_manager:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return permission_set.get_pending(self.request.user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        page_number = self.request.GET.get("page", 1)
        context = super().get_context_data(**kwargs)
        page_obj = Paginator(PermissionLog.objects.values(
            'created',
            'request__system',
            'request__key',
            'request__user__username',
            'created_by__username',
            'comment',
            'approved'
            ).distinct().order_by('-created'), self.log_pagination)
        context['logs'] = page_obj.get_page(page_number)
        return context
