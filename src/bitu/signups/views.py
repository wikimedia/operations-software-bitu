# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Any, Optional

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, UpdateView

from .forms import SignupActivationForm, SignupForm
from .models import Signup
from .tokens import default_token_generator


class SignupFormView(CreateView):
    template_name: str = 'signups_signup.html'
    form_template_name = "form_template.html"
    form_class = SignupForm

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['signup_info_template'] = getattr(settings, 'SIGNUP_INFO_TEMPLATE', '')
        return context


    def get_success_url(self) -> str:
        return reverse('signups:thanks')


INTERNAL_SIGNUP_SESSION_TOKEN = "_signup_reset_token"


class SignupActivationFormView(UpdateView):
    form_class = SignupActivationForm
    template_name: str = 'signups_activation.html'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # Set initial value to true, as the field is hidden.
        # We need to do this in __init__ of the view, as a
        # Boolean fields technically do have an initial value
        # it's just False, so overwriting it in the Form does
        # nothing.
        self.initial['is_active'] = True

    def get_object(self, queryset: Optional[models.query.QuerySet[Any]] = ...) -> Signup:
        uidb64 = self.kwargs.get('uidb64', '')
        pk = urlsafe_base64_decode(uidb64).decode('utf8')
        return Signup.objects.get(pk=pk)

    def get_success_url(self) -> str:
        return reverse('signups:success')

    token_generator = default_token_generator
    reset_url_token = "set-active"

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.signup = self.get_signup(kwargs["uidb64"])
        self.object = self.signup

        if self.signup is not None:
            token = kwargs["token"]
            if token == self.reset_url_token:
                session_token = self.request.session.get(INTERNAL_SIGNUP_SESSION_TOKEN)
                if self.token_generator.check_token(self.signup, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.signup, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_SIGNUP_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(
                        token, self.reset_url_token
                    )
                    return HttpResponseRedirect(redirect_url)

        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_signup(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            signup = Signup.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            Signup.DoesNotExist,
            ValidationError,
        ):
            signup = None
        return signup

    def form_valid(self, form):
        form.save()
        del self.request.session[INTERNAL_SIGNUP_SESSION_TOKEN]
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(SignupActivationFormView, self).get_context_data(**kwargs)
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
