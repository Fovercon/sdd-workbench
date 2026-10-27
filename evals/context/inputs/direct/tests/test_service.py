import unittest
from service import select


class SelectionTests(unittest.TestCase):
    def test_single_exact_record(self):
        item={'id':'A'}
        self.assertEqual(select([item],'A'),[item])
