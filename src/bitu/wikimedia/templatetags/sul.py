from django import template

from wikimedia.validators import wikimedia_global_account

register = template.Library()

@register.inclusion_tag('sul.html', takes_context=True)
def wikimedia_global_account_linking(context):
    return {'linking_wanted': not wikimedia_global_account(context['request'])}
