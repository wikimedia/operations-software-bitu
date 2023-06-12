from django import template

register = template.Library()

@register.filter
def django_message_tags_to_bulma_classes(tags):
    return ' '.join([f'is-{tag}' for tag in tags.split(' ')])

