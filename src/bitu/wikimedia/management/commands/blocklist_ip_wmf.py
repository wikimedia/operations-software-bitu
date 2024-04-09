import ipaddress
import logging

import requests

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from signups.models import BlockListIP


logger = logging.getLogger('bitu')


class Command(BaseCommand):
    name = 'wmf_ip_blocklist'
    help = 'Import IP blocklist from Wikimedia'
    user_agent = {'User-agent': 'Bitu blocklist import (https://idm.wikimedia.org)'}
    uri = 'https://meta.wikimedia.org/w/api.php'
    params = '?action=query&format=json&list=globalblocks&formatversion=2&bglimit=50'
    current_head = BlockListIP.objects.order_by('-created_date').first()

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print blocks to be imported, but do not persist.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if not dry_run:
            self.fetch_data()
        self.removed_expired(dry_run=dry_run)

    def import_result(self, result):
        for item in result:
            if not self.import_item(item):
                print(f'stopping import on: {item}')
                return True

    def import_item(self, item):
        created_date = parse_datetime(item['timestamp'])
        expiry_date = parse_datetime(item['expiry'])
        ip_network = ipaddress.ip_network(item['address'])

        block_list_item, created = BlockListIP.objects.get_or_create(
            created_date=created_date,
            expiry=expiry_date,
            origin=item['bywiki'],
            start=str(ip_network[0].exploded),
            end=str(ip_network[-1].exploded),
            comment=item['reason']
        )

        # Return created, if we didn't create the block list item, that
        # means we've seen it before and can stop the import.
        print(f'item created: {created}, {item}')
        return created

    def fetch_data(self, continuation=''):
        while True:
            uri = self.uri + self.params + continuation
            response = requests.get(
                uri,
                headers=self.user_agent)

            if response.status_code != 200:
                logger.error(f'wmf_ip_blocklist, msg=failed to import, error={response.text}')
                break

            result = response.json()

            stop = self.import_result(result['query']['globalblocks'])

            if stop or len(result['query']['globalblocks']) < 50:
                break

            continuation = "&bgstart=" + response.json()['continue']['bgstart']

    def removed_expired(self, aged_days=60, dry_run=True):
        """
        Cleanup expired blocks, with a buffer of 60 days. The use of blocked IPs should always
        include a check for expiry of the block. Removing the blocks is mostly done as database
        clean up, and the buffer is in place to allow later analysis of previous blocks.
        """
        expiry = timezone.now() - timedelta(days=aged_days)

        if dry_run:
            blocks = BlockListIP.objects.filter(expiry__lt=expiry).order_by('-expiry')
            print(f'Expired, {blocks.count()} block list items.')
            for block in blocks:
                print(f'{block.network.ljust(34)} - expired: {block.expiry}')
            print('-'.ljust(72, '-'))
            print(f'Total of {blocks.count()} block list items expired'.rjust(72))
            print('-'.ljust(72, '-'))
        else:
            BlockListIP.objects.filter(expiry__gt=expiry).delete()
