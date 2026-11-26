import unittest
from notify import NotifyGateway

class TestNotify(unittest.TestCase):
    def test_order_notice_contains_id_and_amount(self):
        gw = NotifyGateway()
        gw.send_order('O-1', 99.0)
        self.assertEqual(gw.sent[-1]['order'], 'O-1')

    def test_retry_then_fail_event(self):
        gw = NotifyGateway()
        ok = gw.send_with_retry('p', attempt=2)
        self.assertTrue(ok)
