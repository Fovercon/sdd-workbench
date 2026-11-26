class RetryPolicy:
    """当前实现:最多 2 次重试,固定间隔 [1, 4] 秒。"""

    def __init__(self):
        self.max_retries = 2
        self.intervals = [1.0, 4.0]

    def attempts(self):
        return 1 + self.max_retries

    def delay_before(self, retry_index):
        # retry_index: 1-based
        return self.intervals[retry_index - 1]
