from django.forms import Form


class GenericCodexForm(Form):
    """GenericCodexForm - Adds Codex CSS attributes and description
    to input fields. This form is only meant to be used as a parent
    for custom forms.

    Args:
        form Form: Django Form class
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add codex stylesheet class.
        for field_name in self.fields:
            field = self.fields[field_name]
            field.widget.attrs['class'] = 'cdx-text-input__input'
            field.widget.attrs['aria-describedby'] = f'cdx-{field_name}'
