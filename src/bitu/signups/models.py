import base64
import ipaddress
import re
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .tokens import SignupActivationTokenGenerator, default_token_generator
from bitu.helpers import capitalize_first

from . import jobs

mark_safe_lazy = lazy(mark_safe, str)

username_validators = [import_string(module) for module in getattr(settings, 'SIGNUP_USERNAME_VALIDATORS', [])]
uid_validators = [import_string(module) for module in getattr(settings, 'SIGNUP_UID_VALIDATORS', [])]
email_validators = [import_string(module) for module in getattr(settings, 'SIGNUP_EMAIL_VALIDATORS', [])]


class Signup(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Developer account usernames are commonly either the same as \
            a user's Wikimedia account username or their real name."
        ),
        validators=username_validators,
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    # uid - Systems username, for systems with stricter rules.
    uid = models.CharField(
        _("SSH access (shell) username"),
        max_length=32,
        unique=True,
        validators=uid_validators,
        blank=False,
        null=True,
        help_text=mark_safe_lazy(_('Your shell username will be used when logging \
            into <a href="https://wikitech.wikimedia.org/wiki/Portal:Toolforge">Toolforge</a>, \
            other <a href="https://wikitech.wikimedia.org/wiki/Portal:Cloud_VPS">Wikimedia VPS</a> \
            or Wikimedia production hosts using <a href="https://en.wikipedia.org/wiki/Secure_Shell">SSH</a>. \
            This name is typically shorter than a wiki username. It must start with a-z, and can \
            only contain lowercase a-z, 0-9 and - characters.')),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    email = models.EmailField(
        _("email"),
        validators=email_validators,
        unique=True,
        help_text=mark_safe_lazy(
            _('Your email must be unique.\
               If you are setting up an account for a bot,\
               please use a dedicated email address or an\
              address suffix, e.g. user+bot@example.com\
              (if your mailserver supports this).')),
        error_messages={
            "unique": _("Email address already in use."),
        },
    )

    def set_password(self, password):
        for name, module in settings.BITU_SUB_SYSTEMS.items():
            if 'password_hash' not in module:
                continue

            hash_func = import_string(module['password_hash'])

            sp = SignupPassword()
            sp.signup = self
            sp.module = name
            sp.value = hash_func(password)
            sp.save()

    def generate_activation_token(self):
        gen: SignupActivationTokenGenerator = default_token_generator
        token = gen.make_token(self)
        return token

    def generate_activation_link(self):
        token = self.generate_activation_token()
        sid = base64.b64encode(bytes(self.pk.hex, 'utf8'))
        url = reverse('signups:activate', kwargs={'token': token, 'uidb64': sid.decode(encoding='utf8')})
        return settings.BITU_DOMAIN + url

    def validate_activation_token(self, token: str) -> bool:
        gen: SignupActivationTokenGenerator = default_token_generator
        valid = gen.check_token(self, token)
        return valid

    def send_activation_link(self):
        jobs.send_activation_email.delay(self)


class SignupPassword(models.Model):
    signup = models.ForeignKey(Signup, on_delete=models.CASCADE)
    module = models.CharField(null=False, max_length=150)
    value = models.CharField(max_length=256)


class BlockListUsername(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    origin = models.CharField(null=False, default='manual', max_length=255)
    regex = models.CharField(null=False, max_length=255)
    comment = models.CharField(null=False, max_length=255)


class BlockListIP(models.Model):
    created_date = models.DateTimeField()
    expiry = models.DateTimeField()
    origin = models.CharField(null=False, default='manual', max_length=255)
    start = models.GenericIPAddressField(null=False)
    end = models.GenericIPAddressField(null=False)
    comment = models.CharField(null=False, max_length=255)

    @property
    def network(self):
        start = ipaddress.ip_address(self.start)
        end = ipaddress.ip_address(self.end)
        return next(ipaddress.summarize_address_range(start, end)).__str__()


# API dummy classes
# The following classes are used as "dummy" classes for the django REST frameworks
# serializers.
class UserValidation(models.Model):
    username = models.CharField(_("username"), max_length=150)
    uid = models.CharField(_("SSH access (shell) username"), max_length=32)
    sanitized = models.CharField(_("sanitized"), max_length=150)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if not self.uid:
            self.uid = re.sub(r'[^A-Za-z 0-9 -]*', '', self.username.replace(' ', '')).lower()[:32]

        # Clients cannot supply the sanitized username, making it always okay to overwrite.
        self.sanitized = capitalize_first(self.username)

    class Meta:
        managed = False
