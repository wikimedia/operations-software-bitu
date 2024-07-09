import re

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def ticket_link(ticket):
    if not hasattr(settings, 'TICKET_SYSTEM'):
        return ticket

    if not re.match(settings.TICKET_SYSTEM['ticket_regex'], ticket):
        return ticket

    url = settings.TICKET_SYSTEM['url_pattern'].format(ticket=ticket)
    return mark_safe(f'<a href="{url}">{ticket} ({settings.TICKET_SYSTEM["name"]})</a>')
