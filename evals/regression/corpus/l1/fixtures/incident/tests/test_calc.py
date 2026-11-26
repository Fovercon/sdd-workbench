import unittest
from calc import round_amount

class TestRound(unittest.TestCase):
    def test_half_up(self):
        self.assertEqual(round_amount(150), 2)
