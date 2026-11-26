import unittest
from retry import RetryPolicy

class TestRetry(unittest.TestCase):
    def test_attempts_total(self):
        self.assertEqual(RetryPolicy().attempts(), 3)

    def test_fixed_intervals(self):
        p = RetryPolicy()
        self.assertEqual(p.delay_before(1), 1.0)
        self.assertEqual(p.delay_before(2), 4.0)
