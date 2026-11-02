import unittest
from exporter import export


class ExportTests(unittest.TestCase):
    def test_existing_bytes(self):
        self.assertEqual(export([{'id': 'A', 'title': 'a,b'}]),
                         'id,title\r\nA,"a,b"\r\n')

    def test_empty_rows(self):
        self.assertEqual(export([]), 'id,title\r\n')
