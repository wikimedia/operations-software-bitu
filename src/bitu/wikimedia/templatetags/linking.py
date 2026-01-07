from django import template

from wikimedia.validators import phabricator_account, wikimedia_global_account

register = template.Library()

@register.inclusion_tag('sul.html', takes_context=True)
def wikimedia_global_account_linking(context):
    return {'linking_wanted': wikimedia_global_account(context['request'])}


@register.inclusion_tag('phabricator.html', takes_context=True)
def phabricator_account_linking(context):
    return {'phabricator_linking_wanted': phabricator_account(context['request'])}
