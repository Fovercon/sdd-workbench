"""Oracle solution for rate-limiter (evaluator-owned)."""
from collections import deque


class TokenBucketLimiter:
    def __init__(self, rate, capacity):
        if rate <= 0 or capacity <= 0:
            raise ValueError('rate and capacity must be positive')
        self.rate = float(rate)
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.last = None

    def _sync(self, now):
        if self.last is None:
            self.last = now
            return
        elapsed = max(0.0, now - self.last)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last = now

    def available(self, now):
        self._sync(now)
        return self.tokens

    def allow(self, now, tokens=1.0):
        if tokens < 0:
            raise ValueError('tokens must be non-negative')
        self._sync(now)
        if tokens > self.tokens:
            return False
        self.tokens -= tokens
        return True


class SlidingWindowLimiter:
    def __init__(self, window, max_events):
        if window <= 0 or max_events <= 0:
            raise ValueError('window and max_events must be positive')
        self.window = float(window)
        self.max_events = int(max_events)
        self.events = deque()

    def allow(self, now):
        while self.events and self.events[0] <= now - self.window:
            self.events.popleft()
        if len(self.events) + 1 > self.max_events:
            return False
        self.events.append(now)
        return True
