from django.core.exceptions import ValidationError
from django.test import TestCase

from signups.models import BlockListUsername
from signups.validators import IsURLValidator, UsernameValidator

class UsernameValidators(TestCase):
    def test_is_domain(self):
        IsURLValidator('plain username')
        IsURLValidator('www.dev')
        self.assertRaises(ValidationError, IsURLValidator, 'https://en.wikipedia.org')


    def test_blocklist(self):
        UsernameValidator('Michael Ancher')
        UsernameValidator('Anne Ancher')
        UsernameValidator('Peder Severin Krøyer')

        block = BlockListUsername(regex=r'M\w* Ancher')
        block.save()

        self.assertRaises(ValidationError, UsernameValidator, 'Michael Ancher')
        UsernameValidator('Anne Ancher')
        UsernameValidator('Peder Severin Krøyer')

        block = BlockListUsername(regex=r'\w* Ancher')
        block.save()

        self.assertRaises(ValidationError, UsernameValidator, 'Michael Ancher')
        self.assertRaises(ValidationError, UsernameValidator, 'Anne Ancher')
        UsernameValidator('Peder Severin Krøyer')

        block = BlockListUsername(regex=r'\w* Severin \w*')
        block.save()

        self.assertRaises(ValidationError, UsernameValidator, 'Peder Severin Krøyer')