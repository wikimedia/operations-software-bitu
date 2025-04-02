from unittest import TestCase
from unittest.mock import Mock

from wikimedia.integrations.gerrit import Gerrit


class GerritTests(TestCase):

    def test_loadResponse_requires_prefix(self):
        with self.assertRaisesRegex(
            Exception,
            'Json magic prefix could not be found in response',
        ):
            Gerrit.loadResponse(Mock(text='{}'))

    def test_loadResponse_removes_prefix(self):
        self.assertEqual(dict(),  Gerrit.loadResponse(Mock(text=')]}\'\n{}')))
