import logging
import re

from datetime import timedelta

import requests

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from signups.models import BlockListUsername


logger = logging.getLogger('bitu')


class Command(BaseCommand):
    name = 'wmf_blocklist'
    max_age_days = 7
    help = 'Import username blocklist from Wikimedia'
    sources = [
        {
            'name': 'wikitech',
            'uri': 'https://wikitech.wikimedia.org/w/api.php?action=parse&formatversion=2&page=MediaWiki%3ATitleblacklist&prop=text&format=json'
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Print blocks to be imported, but do not persist.',
        )

    def handle(self, *args, **options):
        check_mode = options.get('check', False)

        for blocklist in self.sources:
            self.fetch_blocklist(blocklist['name'], blocklist['uri'], check_mode)

        self.expire(check_mode)

    def expire(self, check_mode):
        max_age = timezone.now() - timedelta(days=self.max_age_days)
        blocks = BlockListUsername.objects.filter(origin=self.name, last_modified__lt=max_age).all()

        if check_mode:
            for block in blocks:
                print(f' will delete: {block.regex}')
            return

        blocks.delete()

    def fetch_blocklist(self, name, uri, check_mode):
        response = requests.get(uri)
        content = response.json()['parse']['text']
        soup = BeautifulSoup(content, 'html.parser')

        for p in soup.find_all('pre'):
            for line in p.get_text().split('\n'):
                if line.startswith('#') or not line:
                    continue


                regex = line.split('<')[0].strip()
                if check_mode and regex:
                    print(regex)
                    continue

                # Attempt to validate the regex. We get regex patterns from
                # PHP, and there are some patterns that will not work for us.
                try:
                    m = re.search(regex, 'testuser')
                except re.error as e:
                    logger.warning('invalid blocklist regex: %s; %s' % (regex, e))
                    continue


                block, created = BlockListUsername.objects.get_or_create(
                    regex=regex,
                    comment=f'Import from {name}',
                    origin=self.name
                )

                # Creating a new blocklist item will automatically updated
                # last modified. For existing items, call save() to update
                # last modified timestamp.
                if not created:
                    block.save()
