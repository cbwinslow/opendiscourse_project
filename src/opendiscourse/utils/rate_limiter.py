"""Rate limiter for API requests."""

import time
import threading
from typing import Dict, Optional


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int, period: float = 60.0):
        self.max_requests = max_requests
        self.period = period
        self.tokens = max_requests
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def acquire(self):
        """Acquire a token, blocking if necessary."""
        while True:
            with self._lock:
                now = time.time()
                elapsed = now - self.last_refill
                refill = elapsed / self.period * self.max_requests
                self.tokens = min(self.max_requests, self.tokens + refill)
                self.last_refill = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

            time.sleep(0.1)


class MultiRateLimiter:
    """Manage rate limits for multiple API endpoints."""

    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}

    def get_limiter(self, key: str, max_requests: int, period: float = 60.0) -> RateLimiter:
        if key not in self._limiters:
            self._limiters[key] = RateLimiter(max_requests, period)
        return self._limiters[key]

    def acquire(self, key: str):
        limiter = self._limiters.get(key)
        if limiter:
            limiter.acquire()
