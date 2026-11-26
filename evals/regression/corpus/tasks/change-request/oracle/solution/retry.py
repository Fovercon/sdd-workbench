class RetryPolicy:
    """变更后实现:最多 5 次重试,指数退避 1,2,4,8,16 秒,单次上限 30 秒。"""

    def __init__(self):
        self.max_retries = 5
        self.cap = 30.0

    def attempts(self):
        return 1 + self.max_retries

    def delay_before(self, retry_index):
        if retry_index >= 6:
            return self.cap
        raw = 2.0 ** (retry_index - 1)
        return min(raw, self.cap)
