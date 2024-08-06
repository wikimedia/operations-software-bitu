import logging
import getpass
import sys

from typing import Any
from django.core.management.base import BaseCommand, CommandParser

import bituldap

from wikimedia.integrations.phabricator import PhabClient

logger = logging.getLogger('bitu')


class Command(BaseCommand):
    help = "Block user access to various systems"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('uid', type=str)
        parser.add_argument(
            '--phabricator',
            '-p',
            action='store_true',
            help='Disable user in Phabricator'
        )

    def confirm(self, uid: str, systems: list[str]) -> bool:
        print(f'Please confirm that you want to block user: {uid} for the following systems')
        if 'all' in systems:
            print('     * Phabricator')
        else:
            for system in systems:
                print(f'    * {system.capitalize()}')

        result = input("Confirm with yes/no: ")
        if not result:
            return False
        while len(result) < 1 or result[0].lower() not in "yn":
            result = input("Please answer yes or no: ")
        return result[0].lower() == "y"

    def handle(self, *args: Any, **options: Any):
        uid = options['uid']
        entry  = bituldap.get_user(uid)
        if not entry:
            self.stdout.write(
                self.style.ERROR_OUTPUT(f'No user with uid: {uid} found in LDAP')
            )
            sys.exit(1)

        systems = [key for key in options if key in ['phabricator', 'all'] and options[key]]
        logger.info(f'Running block command as {getpass.getuser()} on uid: {uid} with options \"{" ".join(systems)}\"')

        if not self.confirm(uid, systems):
            sys.exit(0)

        if options['phabricator'] or options['all']:
            print(f"Block access to Phabricator for user {uid}")
            phc = PhabClient()
            try:
                phc.block_user(entry.cn.__str__())
            except Exception as e:
                logger.error(f'Failed to block user: {uid} for Phabricator, error was: {e}. Command executed by: {getpass.getuser()}')
                self.stdout.write(
                    self.style.ERROR_OUTPUT(e)
                )
                sys.exit(1)



