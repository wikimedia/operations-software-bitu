from typing import Any

import bituldap

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from passlib.hash import ldap_salted_sha1 as lsm

from . import jobs
from .forms import (BlockUserSearchForm,
                    ForgotUsernameForm,
                    RequestPasswordResetForm,
                    PasswordResetForm)

from .integrations.ldap import LDAP
from .models import UserBlockEventLog
from .tokens import default_token_generator


INTERNAL_RESET_SESSION_TOKEN = "_password_reset_token"

class ForgotUsernameView(FormView):
    template_name = 'forgot_username.html'
    form_class = ForgotUsernameForm
    success_url = '/'

    def form_valid(self, form) -> HttpResponse:
        valid = super().form_valid(form)
        if valid:
            messages.success(self.request, _('If the provided email address is in our system we will send you an email with your username'))
            jobs.send_forgot_username_email.delay(form.cleaned_data['email'])
        return valid

class RequestPasswordResetView(FormView):
    template_name = 'request_password_reset.html'
    form_class = RequestPasswordResetForm
    success_url = reverse_lazy('wikimedia:password_wait')

    def form_valid(self, form):
        valid = super().form_valid(form)
        if valid:
            jobs.send_email_password_reset.delay(form.cleaned_data['username'])
        return valid

class PasswordResetView(FormView):
    template_name = 'password_reset.html'
    form_class = PasswordResetForm
    success_url = '/'

    token_generator = default_token_generator
    reset_url_token = "set-password"

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_anonymous:
            return HttpResponseRedirect(self.success_url)

        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]
            if token == self.reset_url_token:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(
                        token, self.reset_url_token
                    )
                    return HttpResponseRedirect(redirect_url)

        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = bituldap.get_user(uid)
        except:
            user = None
        return user

    def form_valid(self, form):
        self.user.userPassword = lsm.hash(form.cleaned_data['password1'])
        self.user.entry_commit_changes()
        del self.request.session[INTERNAL_RESET_SESSION_TOKEN]
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context["validlink"] = True
        else:
            context.update(
                {
                    "form": None,
                    "validlink": False,
                }
            )
        return context


class AccountManagersPermissionMixin():
    """Mixin for checking if a user is an account manager and should be able to
    access special functionality, such as account blocking.
    """
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check if the user has signed in, and if the user is in the list
        of account managers. Account managers being specfied in the settings file under
        ACCOUNT_MANAGERS (list).

        This is a MIXIN and cannot be used on it's own. It must always be used as a mixin
        for a class-based view.

        Args:
            request (HttpRequest): Django HttpRequest object.

        Raises:
            PermissionDenied: Return 403 if the user has not signed in or is not an account manager.

        Returns:
            HttpResponse: Django HttpResponse object
        """

        # Regardless of the anonymous user being listed as a account manager, unauthenticated users
        # should not be allowed to block users.
        if not request.user.is_authenticated:
            raise PermissionDenied()

        if not request.user.account_manager:
            raise PermissionDenied()

        # Hand over control to the views internal dispatch.
        return super().dispatch(request, *args, **kwargs)


class BlockUserView(AccountManagersPermissionMixin, CreateView):
    model = UserBlockEventLog
    fields = ['action', 'comment', 'created_by', 'username', 'unset_email']
    template_name = 'wikimedia/block_user.html'
    success_url = reverse_lazy('wikimedia:block_search')
    action = 'block_user'

    def get_ldap_user(self):
        l = LDAP()
        return l.fetch_entry(self.kwargs['username'])

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # Add LDAP user to context.
        # Note that this is NOT a standard Entry objects and those will
        # not have the attributes we're interested in here, those being
        # information on policies/account blocking.
        context = super().get_context_data(**kwargs)
        context['user'] = self.get_ldap_user()
        return context

    def get_success_url(self) -> str:
        # Append query parameter to success_url to let managers easily locate the user.
        # that where just blocked.
        url = super().get_success_url()
        return url + f'?q={self.kwargs["username"]}'

    def get_initial(self) -> dict[str, Any]:
        # Fill in initial form data.
        initial = super().get_initial()
        initial['username'] = self.kwargs['username']
        initial['created_by'] = self.request.user.get_username()
        initial['action'] = self.action
        return initial

    def form_valid(self, form: Any) -> HttpResponse:
        user = bituldap.get_user(self.kwargs['username'])
        if form.is_valid():
            if form.cleaned_data['created_by'] != self.request.user.get_username():
                # Form data manipulated.
                raise PermissionDenied()

            # Ensure that the log message from the form is created first.
            valid = super().form_valid(form)
            self.update_user(user, form.instance)
            return valid

        return super().form_valid(form)

    def update_user(self, user: bituldap.Entry, log: UserBlockEventLog):
        # Flash success message and queue blocking actions.
        messages.add_message(self.request, level=messages.SUCCESS, message=f'{user.cn} scheduled for blocking')
        jobs.update_account(user, self.request.user, log, self.action)


class UnBlockUserView(BlockUserView):
    action = 'unblock_user'
    template_name = 'wikimedia/unblock_user.html'

    def update_user(self, user: bituldap.Entry, log: UserBlockEventLog):
        # Flash success message and queue blocking actions.
        messages.add_message(self.request, level=messages.SUCCESS, message=f'{user.cn} scheduled for unblocking')
        jobs.update_account(user, self.request.user, log, self.action)


class BlockUserSearch(AccountManagersPermissionMixin, FormView):
    form_class = BlockUserSearchForm
    template_name = 'wikimedia/block_user_search.html'
    l = LDAP()

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        # Django doesn't really have a good way to do search view.
        # Intercept post and get Form and misuse is_valid to do the actual search.
        form = self.get_form(self.form_class)
        if form.is_valid():
            return self.form_valid(form, **kwargs)
        return super().post(request, *args, **kwargs)

    def search(self, value):
        # Empty search input.
        if not value:
            return []

        # The search term is probably an email.
        if '@' in value:
            return self.l.query(f'mail: {value}')

        # Search both CN and UID in LDAP and add to entries dict for de-duplication.
        # Bituldap utilized the LDAP3 abstraction layer, which does not easily to OR queries. Instead we do two queries and merge
        # the results based on DN.
        entries = {}
        for entry in self.l.query(f'CommonName: {value}'):
            entries[entry.entry_dn] = entry
        for entry in self.l.query(f'uid:{value}'):
            entries[entry.entry_dn] = entry

        return entries.values()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # Handle returns from block and unblock pages. The q parameter is parsed back to trigger a
        # search for the user currently being blocked/unblocked.
        context = super().get_context_data(**kwargs)
        context["query"] = ""
        context["users"] = []
        if 'q' in self.request.GET:
            context['query'] = self.request.GET['q']
            context['users'] = self.search(self.request.GET['q'])
        return context

    def form_valid(self, form, **kwargs):
        context = self.get_context_data(**kwargs)
        context['form'] = form
        context['users'] = self.search(form.cleaned_data['username'])
        return self.render_to_response(context)


class BlockEventLog(AccountManagersPermissionMixin, ListView):
    model = UserBlockEventLog

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        return qs.filter(username=self.kwargs['username']).order_by('-created_at')


class PublicBlockEventLog(ListView):
    model = UserBlockEventLog
    template_name = 'wikimedia/publicuserblockeventlog_list.html'
    paginate_by = 25

    def get_queryset(self) -> QuerySet[UserBlockEventLog]:
        qs = super().get_queryset()
        return qs.filter(parent=None, action__in=['block_user', 'unblock_user']).order_by('-created_at')