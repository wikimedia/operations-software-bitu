from django import template

register = template.Library()


@register.filter
def django_message_tags_to_codex_classes(tags):
    tags_map = {'info': 'notice',
                'success': 'success',
                'warning': 'warning',
                'error': 'error',
                'debug': 'notice',
                'safe': ''
                }

    return ' '.join([f'cdx-message--{tags_map[tag]}' for tag in tags.split(' ')])
