"""限流器库(待实现,见 docs/PRD.md)。"""


class TokenBucketLimiter:
    def __init__(self, rate, capacity):
        raise NotImplementedError

    def allow(self, now, tokens=1.0):
        raise NotImplementedError

    def available(self, now):
        raise NotImplementedError


class SlidingWindowLimiter:
    def __init__(self, window, max_events):
        raise NotImplementedError

    def allow(self, now):
        raise NotImplementedError
