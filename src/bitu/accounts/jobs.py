import base64
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_rq import job


from .models import User, EmailUpdate
from .tokens import BituUpdateEmailTokenGenerator

logger = logging.getLogger('bitu')


@job
def send_update_email_request(user: User, email):
    data = EmailUpdate(user=user, email=email)
    token = BituUpdateEmailTokenGenerator().make_token(data)
    uidb64 = base64.b64encode(bytes(f'{user.pk};{email}', 'utf8'))
    url = reverse('accounts:email_verify', kwargs={'token': token, 'uidb64': uidb64.decode(encoding='utf8')})
    timeout = int(settings.PASSWORD_RESET_TIMEOUT / 60)  # From seconds to minutes.
    plaintext = get_template('email/email_update.txt')
    html = get_template('email/email_update.html')
    context = {
        'url': settings.BITU_DOMAIN + url,
        'timeout': timeout,
        'old_email': user.email,
        'new_email': email,
        'username': user.get_username()
    }
    subject =  _('Updating the email address of your Wikimedia Developer Account')
    from_email = settings.BITU_NOTIFICATION['default_sender']
    to_email = email
    msg = EmailMultiAlternatives(subject,
                                 plaintext.render(context),
                                 from_email,
                                 [to_email])
    msg.attach_alternative(html.render(context), 'text/html')
    msg.send()
    logger.info('sending email update message to user: %s, email: %s', user.get_username(), to_email)