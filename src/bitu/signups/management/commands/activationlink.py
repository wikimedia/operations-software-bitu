# SPDX-License-Identifier: GPL-3.0-or-later
import sys

from django.core.management.base import BaseCommand

from signups.models import Signup


class Command(BaseCommand):
    help = 'Generate activation link for new user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--uid',
            type=str,
            help='Generate activation link for username'
        )

        parser.add_argument(
            '--email',
            type=str,
            help='Generate activation link for email address'
        )

        parser.add_argument(
            '--uuid',
            type=str,
            help='Generate activation link for UUID'
        )

        parser.add_argument(
            '--list',
            action='store_true',
            help='List signups.',
        )

    def handle(self, *args, **options):
        if options['list']:
            for signup in Signup.objects.all():
                print(f"PK: {signup.pk} - {signup.uid} ({signup.email}) ")
            sys.exit(0)

        if not options['uid'] and not options['email'] and not options['uuid']:
            self.print_help('manage.py', 'activationlink')
            sys.exit(1)

        if options['uid']:
            signups = Signup.objects.filter(uid=options['uid'])
        elif options['email']:
            signups = Signup.objects.filter(email=options['email'])
        elif options['uuid']:
            signups = Signup.objects.filter(pk=options['uuid'])

        if len(signups) > 1:
            print("Multiple signups found, please specify UUID")
            for signup in signups:
                print(f"PK: {signup.pk} - {signup.uid} ({signup.email}) ")
            sys.exit(1)

        if len(signups) == 0:
            print("No signups found. Use --list to view all signups in the database")
            self.print_help('manage.py', 'activationlink')
            sys.exit(1)

        print(signups.first().generate_activation_link())
