
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

from .integrations import gitlab, gerrit, ldap, phabricator
from .models import UserBlockEventLog
from .tokens import default_token_generator

logger = logging.getLogger('bitu')
User = get_user_model()


@job
def update_ldap_attributes(user: 'User', attributes:Dict):
    ldap_user = bituldap.get_user(user.get_username())
    if not ldap_user:
        logger.warning(f'user: {user.get_username()} not found in ldap')
        return

    for k, v in attributes.items():
        setattr(ldap_user, k, v)
        ldap_user.entry_commit_changes()

    logger.info(f'update ldap user: {ldap_user} with attributes: {attributes}')


@job('notification')
def send_email_password_reset(username):
    config = bituldap.read_configuration()
    ldap_user: Union[Entry, None] = bituldap.get_single_object(
        config.users, 'cn', username)

    if not ldap_user:
        return

    if not ldap_user.mail.value:
        logger.warning('password reset requested for user: %s, but no email address is defined in LDAP', username)

    token = default_token_generator.make_token(ldap_user)
    uid = base64.b64encode(bytes(ldap_user.uid.value, 'utf8'))
    url = reverse('wikimedia:reset', kwargs={'token': token, 'uidb64': uid.decode(encoding='utf8')})

    timeout = int(settings.PASSWORD_RESET_TIMEOUT / 60)  # From seconds to minutes.

    plaintext = get_template('email/email_password_reset.txt')
    html = get_template('email/email_password_reset.html')
    context = {'url': settings.BITU_DOMAIN + url , 'timeout': timeout}
    subject = _('Password reset')
    from_email = settings.BITU_NOTIFICATION['default_sender']
    to_email = ldap_user.mail

    msg = EmailMultiAlternatives(subject,
                                 plaintext.render(context),
                                 from_email,
                                 [to_email])
    msg.attach_alternative(html.render(context), 'text/html')
    msg.send()
    logger.info('sending password reset to user: %s, email: %s', username, to_email)


@job('notification')
def send_forgot_username_email(email):
    config = bituldap.read_configuration()
    entry = bituldap.get_single_object(config.users, 'mail', email)
    if not entry:
        logger.info(f'request for username, by unknown email: {email}')
        return

    plaintext = get_template('email/forgot_username.txt')
    html = get_template('email/forgot_username.html')
    context = {'site': settings.BITU_DOMAIN, 'username': entry.uid}
    subject = _('Reminder for your Wikimedia Developer username')
    from_email = settings.BITU_NOTIFICATION['default_sender']
    msg = EmailMultiAlternatives(subject,
                                 plaintext.render(context),
                                 from_email,
                                 [email])
    msg.attach_alternative(html.render(context), 'text/html')
    msg.send()
    logger.info('sending username reminder to user: %s, email: %s', entry.uid, email)


@job('default')
def update_account(entry: bituldap.Entry, manager: 'User', action: str):
    """Block account across systems, given an LDAP username

    Args:
        username (Entry): LDAP Entry
    """
    uid = entry.uid.__str__()
    if action not in ['block_user', 'unblock_user']:
        logger.error(f'user account block/unblock action unknown, user: {uid}')
        return

    clients = {
        'ldap': {'client': ldap.LDAP(), 'user': uid},
        'gerrit': {'client': gerrit.Gerrit(), 'user': entry.cn.__str__() },
        'gitlab': {'client': gitlab.Gitlab(), 'user': entry.cn.__str__()},
        'phabricator': {'client': phabricator.PhabClient(), 'user': entry.cn.__str__() },
    }

    for name, options in clients.items():
        try:
            client = options['client']
            user = options['user']
            func = getattr(client, action)
            func(user)

            logger.info(f'user block/unblock success, system: {name}, action: {action}, user: {uid}, manager: {manager.get_username()}')
            UserBlockEventLog.objects.create(
                username=uid,
                created_by=manager.get_username(),
                action=f'{name} {action}',
                comment=f'Successfully updated in {name}, action was {action}'
            )
        except Exception as e:
            logger.error(f'user block/unblock failed, system: {name}, action: {action}, user: {uid}, manager: {manager.get_username()}, error: {e}')
            UserBlockEventLog.objects.create(
                username=uid,
                created_by=manager.get_username(),
                action=f'{name} {action}',
                comment=f'Failed: {e}'
            )
