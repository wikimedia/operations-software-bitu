# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect


from .forms import UpdateEmailForm, VerifyEmailForm
from .models import User, EmailUpdate, Token
from . import jobs, tokens

from bitu.views import ObjectAccessRestrictMixin


INTERNAL_EMAIL_UPDATE_SESSION_TOKEN = "_email_update_token"


class UpdateEmailView(FormView):
    form_class = UpdateEmailForm
    template_name = 'update_email.html'
    success_url = '/'

    def form_valid(self, form):
        valid = super().form_valid(form)
        if valid:
            messages.info(self.request, _('An email with a verification link has been sent to %(email)s.') % {
                'email': form.cleaned_data['email2']})
            jobs.send_update_email_request.delay(self.request.user, form.cleaned_data['email2'])
        return valid


class VerifyEmailView(FormView):
    form_class = VerifyEmailForm
    template_name = 'verify_email.html'
    success_url = '/'

    token_generator = tokens.BituUpdateEmailTokenGenerator()
    reset_url_token = "set-email"

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if self.request.user.is_anonymous:
            return HttpResponseRedirect('/')

        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.user, self.email = self.get_data(kwargs["uidb64"])

        if self.user != self.request.user:
            raise PermissionDenied()

        data = EmailUpdate(user=self.user, email=self.email)

        if self.user is not None:
            token = kwargs["token"]
            if token == self.reset_url_token:
                session_token = self.request.session.get(INTERNAL_EMAIL_UPDATE_SESSION_TOKEN)
                if self.token_generator.check_token(data, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(data, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_EMAIL_UPDATE_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(
                        token, self.reset_url_token
                    )
                    return HttpResponseRedirect(redirect_url)

        # Display the "email reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_data(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            pk, email = urlsafe_base64_decode(uidb64).decode().split(';')
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            user = None
        return user, email

    def get_initial(self):
        initial = super().get_initial()
        initial['user_id'] = self.request.user.pk
        initial['email'] = self.email
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context["validlink"] = True
            context["email"] = self.email
        else:
            context.update(
                {
                    "form": None,
                    "validlink": False,
                }
            )
        return context

    def form_valid(self, form):
        valid = super().form_valid(form)

        user_id = form.cleaned_data.get("user_id")

        # Avoid users manipulating POST/Form data and changing the
        # email address of other users.
        if user_id != self.request.user.id:
            raise PermissionDenied()

        if valid:
            email = form.cleaned_data.get("email")
            user = User.objects.get(pk=user_id)
            user.email = email
            user.save()
            messages.success(self.request, _(
                'Email address successfully updated. \
                Please allow for a few minutes for the change to propagate.'))
        return valid


class TokensListView(ObjectAccessRestrictMixin, ListView):
    model = Token


class TokenCreateView(CreateView):
    model = Token
    fields = ['comment',]
    success_url = reverse_lazy('accounts:api_tokens')

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.user = self.request.user
        form.save()
        valid = super().form_valid(form)
        if valid:
            messages.success(self.request, _(
                "New API created, please note down your key, it will not be shown again. \
                Token: <strong>%(key)s</strong>, comment: %(comment)s" %
                {'key': form.instance.key, 'comment': form.instance.comment}), extra_tags='safe')
        else:
            messages.error(self.request, _('Failed to create new API token'))
        return valid


class TokenDeleteView(ObjectAccessRestrictMixin, DeleteView):
    model = Token
    success_url = reverse_lazy('accounts:api_tokens')

    def delete(self, request, *args, **kwargs):
        messages.add_message(request, messages.INFO, _('SSH key successfully deleted.'))
        return super().delete(request, *args, **kwargs)
