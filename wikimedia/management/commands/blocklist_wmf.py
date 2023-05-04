import requests

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from signups.models import BlockListUsername


class Command(BaseCommand):
    help = 'Import username blocklist from Wikimedia'
    BLOCK_LIST_URI = 'https://wikitech.wikimedia.org/w/api.php?action=parse&formatversion=2&page=MediaWiki%3ATitleblacklist&prop=text&format=json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Print blocks to be imported, but do not persist.',
        )

    def handle(self, *args, **options):
        response = requests.get(self.BLOCK_LIST_URI)
        content = response.json()['parse']['text']
        soup = BeautifulSoup(content, 'html.parser')

        for p in soup.find_all('pre'):
            for line in p.get_text().split('\n'):
                if line.startswith('#') or not line:
                    continue

                regex = line.split(' ')[0]
                if options['check']:
                    print(regex)
                    continue
                BlockListUsername.objects.get_or_create(
                    regex=regex,
                    comment='Import from meta.wikimedia.org'
                )
