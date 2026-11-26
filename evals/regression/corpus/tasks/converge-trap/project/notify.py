class NotifyGateway:
    def __init__(self):
        self.sent = []
        self.failures = []

    def send_order(self, order_id, amount):
        self.sent.append({'order': order_id, 'amount': amount})
        return True

    def send_with_retry(self, payload, attempt, fail_first=False):
        if fail_first and attempt < 2:
            return False
        self.sent.append(payload)
        return True
