import bituldap

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView

from . import jobs
from .forms import RequestPasswordResetForm, PasswordResetForm
from .tokens import default_token_generator

INTERNAL_RESET_SESSION_TOKEN = "_password_reset_token"


class RequestPasswordResetView(FormView):
    template_name = 'request_password_reset.html'
    form_class = RequestPasswordResetForm
    success_url = reverse_lazy('wikimedia:password_wait')

    def form_valid(self, form):
        valid = super().form_valid(form)
        jobs.send_email_password_reset.delay('acarr')
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
        bituldap.set_user_password(self.user.entry_dn, form.cleaned_data['password1'])
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