from typing import Union

from django.conf import settings
from django.core.validators import RegexValidator
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import PermissionRequest


# This seems a little unnecessary, but the ticket validator is added runtime,
# and is not suppose to be included in any migrations. Given this requirement
# the only remaining option is to add it to our form field right before running
# is_valid().
class PermissionRequestForm(ModelForm):
    def _validate_ticket(self) -> Union[RegexValidator, bool]:
        """Create and configure a RegExValidator for the ticket field.
        Returns False if no regex has been defined.

        Returns:
            RegexValidator|bool: RegexValidator or False
        """

        # No ticket system has been defined.
        if not hasattr(settings, 'TICKET_SYSTEM'):
            return False

        # Ticket system does not provide a validator.
        if 'ticket_regex' not in settings.TICKET_SYSTEM:
            return False

        return RegexValidator(
            settings.TICKET_SYSTEM['ticket_regex'],
            _('Invalid ticket format'))

    def is_valid(self) -> bool:
        # Create and append RegExValidator to ticket field.
        ticket_validator = self._validate_ticket()
        if ticket_validator:
            self.fields['ticket'].validators.append(ticket_validator)

        # Run is_valid, which will not pickup our new validator.
        return super().is_valid()

    class Meta:
        model = PermissionRequest
        fields = ['ticket', 'comment']
