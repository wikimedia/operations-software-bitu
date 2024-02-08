from typing import Dict

from django import template
from django.utils.html import format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter
def tooltip(attribute: Dict) -> SafeString:
    """Generate HTML for tooltips.

    Each LDAP attribute can be configured with a tooltip,
    this tag will generate the appropriate HTML.

    Args:
        attribute (dict[str, str]): LDAP attribute configuration from settings.

    Returns:
        SafeString: html for tooltip
    """

    if 'tooltip' not in attribute:
        return ''

    return format_html(
        '<sup class="has-tooltip-multiline" data-tooltip="{}">?</sup>',
        attribute["tooltip"]
    )


@register.filter
def ldap_value(attribute: Dict) -> str:
    if attribute['name'] == 'wikimediaGlobalAccountName' and str(attribute['value']) == '[]':
        return _('Account not linked')
    elif attribute['value'] == '[]':
        return ''
    return attribute['value']


@register.filter
def action(attribute: Dict) -> SafeString:
    """Generate 'action' link for an LDAP attribute.

    If the attribute value is empty, action_label2 is displayed,
    if defined, otherwise display action_label is used. When no
    actions are defined, no HTML is generated.

    Args:
        attribute (dict): LDAP attribute configuration from settings.
    Returns:
        SafeString: html for action link (<a> tag).
    """

    if 'action' not in attribute:
        return ''

    label = attribute.get('action_label', '')
    href = attribute.get('action', '')
    if not attribute['value']:
        label = attribute.get('action_label2', label)

    return format_html(
        '<small class="field-action"><a href="{}">{}</a></small>',
        href,
        label
    )
