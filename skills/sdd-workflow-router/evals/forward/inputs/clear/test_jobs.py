import unittest
from jobs import select_retry, progress

class ExistingSmoke(unittest.TestCase):
    def test_types(self):
        self.assertIsInstance(select_retry([]), list)
        self.assertIsInstance(progress([]), int)
