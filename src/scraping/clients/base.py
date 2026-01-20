"""Base protocol and shared retry configuration for scraper clients."""

from typing import Protocol

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Retry configuration constants
MAX_RETRIES = 3
RETRY_MIN_WAIT = 1.0  # seconds
RETRY_MAX_WAIT = 10.0  # seconds
RETRY_MULTIPLIER = 2.0  # exponential factor


class ScraperClient(Protocol):
    """Protocol defining the interface for async scraper clients."""

    async def fetch_event(self, event_id: str) -> dict:
        """Fetch single event data.

        Args:
            event_id: Platform-specific event identifier.

        Returns:
            Raw API response as dict.
        """
        ...

    async def check_health(self) -> bool:
        """Check if the API is reachable.

        Returns:
            True if healthy, False otherwise.
        """
        ...


def create_retry_decorator():
    """Create a configured tenacity @retry decorator.

    Returns:
        Configured retry decorator with exponential backoff.
    """
    return retry(
        retry=retry_if_exception_type(
            (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError)
        ),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(
            multiplier=RETRY_MULTIPLIER,
            min=RETRY_MIN_WAIT,
            max=RETRY_MAX_WAIT,
        ),
        reraise=True,
    )
