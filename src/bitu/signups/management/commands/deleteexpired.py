# SPDX-License-Identifier: GPL-3.0-or-later
from django.core.management.base import BaseCommand
from signups.models import Signup
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Delete expired signup requests.'

    def add_arguments(self, parser):
        parser.add_argument('days', type=int, default=30, help='Maximum number of days to keep.')
        parser.add_argument(
            '--check',
            action='store_true',
            help='List signups eligible for deletion.',
        )

    def handle(self, *args, **options):

        today = timezone.now()
        expire_date = today - timedelta(days=options['days'])

        signups = Signup.objects.filter(created_date__lt=expire_date)

        if options['check']:
            for signup in signups:
                self.stdout.write(
                    self.style.ERROR(
                        f"- {signup.username}; {signup.email} {signup.created_date}"))
            return

        signups.delete()
