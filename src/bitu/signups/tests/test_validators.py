from django.core.exceptions import ValidationError
from django.test import TestCase

from signups.models import BlockListUsername
from signups.validators import IsDomainValidator, UsernameValidator

class UsernameValidators(TestCase):
    def test_is_domain(self):
        IsDomainValidator('plain username')
        IsDomainValidator('www.dev')
        self.assertRaises(ValidationError, IsDomainValidator, 'https://en.wikipedia.org')


    def test_blocklist(self):
        UsernameValidator('Michael Ancher')
        UsernameValidator('Anne Ancher')
        UsernameValidator('Peder Severin Krøyer')

        block = BlockListUsername(regex='M\w* Ancher')
        block.save()

        self.assertRaises(ValidationError, UsernameValidator, 'Michael Ancher')
        UsernameValidator('Anne Ancher')
        UsernameValidator('Peder Severin Krøyer')

        block = BlockListUsername(regex='\w* Ancher')
        block.save()

        self.assertRaises(ValidationError, UsernameValidator, 'Michael Ancher')
        self.assertRaises(ValidationError, UsernameValidator, 'Anne Ancher')
        UsernameValidator('Peder Severin Krøyer')

        block = BlockListUsername(regex='\w* Severin \w*')
        block.save()

        self.assertRaises(ValidationError, UsernameValidator, 'Peder Severin Krøyer')