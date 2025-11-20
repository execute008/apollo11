"""Rate limiter to prevent hitting API limits and getting banned."""

import time
import logging
from typing import Optional, Callable
from functools import wraps
from threading import Lock
from collections import deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter to control API request rates.

    Prevents hitting API rate limits and getting temporary bans.
    """

    def __init__(
        self,
        max_calls: int = 100,
        period: int = 60,
        burst: Optional[int] = None
    ):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum calls allowed in period
            period: Time period in seconds
            burst: Max burst size (default: max_calls)
        """
        self.max_calls = max_calls
        self.period = period
        self.burst = burst or max_calls

        self.calls = deque()
        self.lock = Lock()

        logger.info(f"Rate limiter initialized: {max_calls} calls/{period}s")

    def __call__(self, func: Callable) -> Callable:
        """Allow using as decorator."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait_if_needed()
            return func(*args, **kwargs)

        return wrapper

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        with self.lock:
            now = time.time()

            # Remove old calls outside the window
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            # Check if we need to wait
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.period - now

                if sleep_time > 0:
                    logger.warning(f"Rate limit reached. Waiting {sleep_time:.2f}s...")
                    time.sleep(sleep_time)

                    # Clean up again after waiting
                    now = time.time()
                    while self.calls and self.calls[0] < now - self.period:
                        self.calls.popleft()

            # Record this call
            self.calls.append(now)

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        with self.lock:
            now = time.time()

            # Count recent calls
            recent_calls = sum(1 for call_time in self.calls if call_time > now - self.period)

            return {
                "max_calls": self.max_calls,
                "period": self.period,
                "recent_calls": recent_calls,
                "remaining_calls": max(0, self.max_calls - recent_calls),
                "utilization": (recent_calls / self.max_calls) * 100 if self.max_calls > 0 else 0
            }

    def reset(self):
        """Reset the rate limiter."""
        with self.lock:
            self.calls.clear()
            logger.info("Rate limiter reset")


# Pre-configured rate limiters for different services
_rate_limiters = {}


def get_rate_limiter(name: str, max_calls: int = 100, period: int = 60) -> RateLimiter:
    """
    Get or create a named rate limiter.

    Args:
        name: Rate limiter name (e.g., 'apollo', 'elevenlabs')
        max_calls: Max calls per period
        period: Period in seconds

    Returns:
        RateLimiter instance
    """
    if name not in _rate_limiters:
        _rate_limiters[name] = RateLimiter(max_calls=max_calls, period=period)

    return _rate_limiters[name]


def rate_limit(name: str = "default", max_calls: int = 100, period: int = 60):
    """
    Decorator for rate limiting functions.

    Usage:
        @rate_limit("apollo", max_calls=10, period=60)
        def call_apollo_api():
            pass
    """
    def decorator(func: Callable) -> Callable:
        limiter = get_rate_limiter(name, max_calls, period)

        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait_if_needed()
            return func(*args, **kwargs)

        return wrapper

    return decorator
