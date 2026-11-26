import unittest
from src.app import render_notification


class TestNotification(unittest.TestCase):
    def test_order_and_amount(self):
        text = render_notification('A', 12)
        self.assertIn('A', text)
        self.assertIn('12.00', text)
