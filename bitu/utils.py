from django.conf import settings
from django.core.mail import EmailMultiAlternatives

import logging

logger = logging.getLogger('bitu')


def send_service_message(subject: str, message: str, limited:bool = False):
    """Send error messages to the administrators.

    Args:
        subject (str): email subject
        message (str): message content
        limited (bool): send email to a subset of admins as defined by ADMINS_LIMITED
    """

    admins = []
    # Fallback to all admins if limited was requested but settings is not defined.
    if limited and hasattr(settings, 'ADMINS_LIMITED'):
        logger.info('Sending message with subject: %s to limited admins', subject)
        admins = settings.ADMINS_LIMITED

        # Admins is defined, but empty and 'limited' is considered disabled.
        if not admins:
            return

    elif hasattr(settings, 'ADMINS'):
        admins = settings.ADMINS

    if not admins:
        logger.warning('Error sending service message, admins not defined.')
        return

    msg = EmailMultiAlternatives(subject=f'[BITU] {subject}',
                                 body=message,
                                 from_email='sre-foundations@wikimedia.org',
                                 to=admins)

    msg.attach_alternative(message, "text/html")
    msg.send()
