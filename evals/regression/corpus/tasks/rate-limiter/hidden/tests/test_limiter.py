import unittest

from limiter import SlidingWindowLimiter, TokenBucketLimiter


class TestTokenBucket(unittest.TestCase):
    def test_starts_full(self):
        bucket = TokenBucketLimiter(1.0, 3.0)
        for _ in range(3):
            self.assertTrue(bucket.allow(0.0))

    def test_reject_when_empty_no_consume(self):
        bucket = TokenBucketLimiter(1.0, 1.0)
        self.assertTrue(bucket.allow(0.0))
        self.assertFalse(bucket.allow(0.0))
        self.assertFalse(bucket.allow(0.0))
        self.assertAlmostEqual(bucket.available(0.0), 0.0)

    def test_refill_over_time(self):
        bucket = TokenBucketLimiter(2.0, 4.0)
        for _ in range(4):
            self.assertTrue(bucket.allow(0.0))
        self.assertAlmostEqual(bucket.available(1.5), 3.0)

    def test_available_does_not_consume(self):
        bucket = TokenBucketLimiter(1.0, 2.0)
        bucket.allow(0.0, 2.0)
        self.assertAlmostEqual(bucket.available(1.0), 1.0)
        self.assertAlmostEqual(bucket.available(1.0), 1.0)
        self.assertTrue(bucket.allow(1.0))

    def test_partial_refill_then_reject(self):
        bucket = TokenBucketLimiter(1.0, 2.0)
        bucket.allow(0.0, 2.0)
        self.assertFalse(bucket.allow(1.5, 2.0))
        self.assertTrue(bucket.allow(1.5, 1.5))

    def test_constructor_validation(self):
        with self.assertRaises(ValueError):
            TokenBucketLimiter(0, 1)
        with self.assertRaises(ValueError):
            TokenBucketLimiter(1, 0)
        with self.assertRaises(ValueError):
            TokenBucketLimiter(-1, 1)

    def test_negative_tokens_raises(self):
        bucket = TokenBucketLimiter(1.0, 2.0)
        with self.assertRaises(ValueError):
            bucket.allow(0.0, -0.1)


class TestSlidingWindow(unittest.TestCase):
    def test_within_window_limit(self):
        limiter = SlidingWindowLimiter(10, 2)
        self.assertTrue(limiter.allow(1.0))
        self.assertTrue(limiter.allow(2.0))
        self.assertFalse(limiter.allow(3.0))
        self.assertFalse(limiter.allow(4.0))

    def test_rejected_not_recorded(self):
        limiter = SlidingWindowLimiter(10, 1)
        self.assertTrue(limiter.allow(1.0))
        self.assertFalse(limiter.allow(1.5))
        self.assertTrue(limiter.allow(11.5))

    def test_boundary_strictly_greater(self):
        limiter = SlidingWindowLimiter(10, 1)
        self.assertTrue(limiter.allow(5.0))
        # exactly now-window (5.0) is outside the kept window -> allowed
        self.assertTrue(limiter.allow(15.0))

    def test_duplicate_timestamps_independent(self):
        limiter = SlidingWindowLimiter(5, 2)
        self.assertTrue(limiter.allow(1.0))
        self.assertTrue(limiter.allow(1.0))
        self.assertFalse(limiter.allow(1.0))

    def test_constructor_validation(self):
        with self.assertRaises(ValueError):
            SlidingWindowLimiter(0, 1)
        with self.assertRaises(ValueError):
            SlidingWindowLimiter(10, 0)
