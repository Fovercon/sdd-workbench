import unittest
from retry import RetryPolicy


class TestNewRetrySpec(unittest.TestCase):
    def test_attempts_total_six(self):
        self.assertEqual(RetryPolicy().attempts(), 6)

    def test_exponential_backoff(self):
        p = RetryPolicy()
        self.assertEqual([p.delay_before(i) for i in range(1, 6)],
                         [1.0, 2.0, 4.0, 8.0, 16.0])

    def test_cap_30s(self):
        p = RetryPolicy()
        self.assertEqual(p.delay_before(6), 30.0)
        self.assertEqual(p.delay_before(9), 30.0)
