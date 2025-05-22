# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Any

from django_rq import job
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template


def load_templates() -> dict[str:Any]:
    name = settings.BITU_NOTIFICATION.get('signup_template_prefix',
                                          'email_signup_activation')
    plaintext = f'email/{name}.txt'
    html = f'email/{name}.html'
    return {'plaintext': get_template(plaintext),
            'html': get_template(html)}


@job('notification')
def send_activation_email(signup):
    timeout = settings.PASSWORD_RESET_TIMEOUT / 60  # From seconds to minutes.

    templates = load_templates()
    context = {'url': signup.generate_activation_link(), 'timeout': timeout}
    subject = settings.BITU_NOTIFICATION.get('signup_subject', 'Bitu IDM account activation')
    from_email = settings.BITU_NOTIFICATION['default_sender']
    to_email = signup.email

    msg = EmailMultiAlternatives(subject,
                                 templates['plaintext'].render(context),
                                 from_email,
                                 [to_email])
    msg.attach_alternative(templates['html'].render(context), "text/html")
    msg.send()
