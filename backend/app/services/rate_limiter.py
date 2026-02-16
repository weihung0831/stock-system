"""Rate limiting utility for API requests."""
import time
import logging
from typing import Callable, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with retry logic for API requests."""

    def __init__(self, max_requests_per_hour: int = 600):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_hour: Maximum requests allowed per hour
        """
        self.max_requests = max_requests_per_hour
        self.request_interval = 3600 / max_requests_per_hour
        self.last_request_time = 0.0
        self.request_count = 0
        self.hour_start_time = time.time()

    def enforce(self) -> None:
        """Enforce rate limiting before making a request."""
        current_time = time.time()

        # Reset counter every hour
        if current_time - self.hour_start_time >= 3600:
            self.request_count = 0
            self.hour_start_time = current_time

        # Check if we've hit the limit
        if self.request_count >= self.max_requests:
            sleep_time = 3600 - (current_time - self.hour_start_time)
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self.request_count = 0
                self.hour_start_time = time.time()

        # Throttle individual requests
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)

        self.last_request_time = time.time()
        self.request_count += 1

    def retry_request(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Execute request with retry logic and exponential backoff.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            DataFrame or None if all retries failed
        """
        max_retries = 3
        retry_delays = [2, 4, 8]  # Exponential backoff

        for attempt in range(max_retries):
            try:
                self.enforce()
                result = func(*args, **kwargs)
                if result is not None and not result.empty:
                    return result
                logger.warning(f"Empty result on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delays[attempt])
                    continue
                else:
                    logger.error(f"All retries failed for {func.__name__}")
                    return None

        return None
