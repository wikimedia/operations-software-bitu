
import base64
import logging

from typing import Dict, Union

import bituldap

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext as _
from django_rq import job
from ldap3 import Entry

from .tokens import default_token_generator

logger = logging.getLogger('bitu')
User = get_user_model()


@job
def update_ldap_attributes(user:'User', attributes:Dict):
    ldap_user = bituldap.get_user(user.get_username())
    if not ldap_user:
        logger.warning(f'user: {user.get_username()} not found in ldap')
        return

    for k,v in attributes.items():
        setattr(ldap_user, k, v)
        ldap_user.entry_commit_changes()

    logger.info(f'update ldap user: {ldap_user} with attributes: {attributes}')


@job('notification')
def send_email_password_reset(username):
    ldap_user: Union[Entry, None] = bituldap.get_user(username)
    if not ldap_user:
        return

    token = default_token_generator.make_token(ldap_user)
    uid = base64.b64encode(bytes(ldap_user.uid.value, 'utf8'))
    url = reverse('wikimedia:reset', kwargs={'token': token, 'uidb64': uid.decode(encoding='utf8')})
    
    timeout = settings.PASSWORD_RESET_TIMEOUT / 60  # From seconds to minutes.

    plaintext = get_template('email/email_signup_activation.txt')
    html = get_template('email/email_signup_activation.html')
    context = { 'url': settings.BITU_DOMAIN + url , 'timeout': timeout }    
    subject =  _('Account activation')
    from_email = settings.BITU_NOTIFICATION_DEFAULT_SENDER
    to_email = ldap_user.email
    
    msg = EmailMultiAlternatives(subject,
                                 plaintext.render(context),
                                 from_email, 
                                 [to_email])
    msg.attach_alternative(html.render(context), "text/html")
    msg.send()

