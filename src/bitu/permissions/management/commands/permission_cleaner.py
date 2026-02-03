# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sys

from datetime import timedelta
from typing import Any
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from permissions.models import PermissionRequest

logger = logging.getLogger('bitu')


class Command(BaseCommand):
    help = "Expire old permission requests, which were newer approved or handled"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--limit',
                            type=int,
                            default=30,
                            help='Maximum lifetime, in days'
                            )
        parser.add_argument(
            '--dry-run',
            '-d',
            action='store_true',
            help='Dry-Run, print only'
        )

    def handle(self, *args: Any, **options: Any):
        dry_run = options.get('dry_run', False)

        expire = timezone.now() - timedelta(days=options["limit"])

        requests = PermissionRequest.objects \
            .filter(created__lt=expire) \
            .filter(status=PermissionRequest.PENDING)

        if dry_run:
            print("======================== DRY-RUN ========================")

            if not requests:
                print("No expired requests")
                sys.exit(0)

            print("The following requests have expired and can be cancelled:")
            for r in requests:
                print(r)
            sys.exit(0)

        for r in requests:
            r.status = r.CANCELLED
            r.save()

