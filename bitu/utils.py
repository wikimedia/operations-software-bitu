from django.conf import settings
from django.core.mail import EmailMultiAlternatives

import logging


def send_service_message(subject: str, message: str):
    """Send error messages to the administrators.

    Args:
        subject (str): email subject
        message (str): message content
    """

    if not hasattr(settings, 'ADMINS'):
        logging.warning('Error sending service message, admins not defined.')
        return

    msg = EmailMultiAlternatives(f'BITU ERROR: {subject}',
                                 message,
                                 'sre-foundations@wikimedia.org',
                                 settings.ADMINS)
    msg.send()
