"""Exception hierarchy for scraper clients.

Provides a typed exception hierarchy for distinguishing between different
failure modes during scraping:

- ScraperError: Base class for all scraper exceptions
- InvalidEventIdError: Event not found (404) or invalid ID format
- NetworkError: Connection timeout, DNS failure, or network unreachable
- ApiError: Unexpected response structure or business logic error
- RateLimitError: HTTP 429 or platform-specific rate limit response

Usage:
    All scraper clients raise these exceptions. The EventCoordinator
    catches them to update per-event error tracking without failing
    the entire batch.

    try:
        data = await client.fetch_event(event_id)
    except InvalidEventIdError:
        # Event gone or ID changed - log and skip
    except NetworkError:
        # Transient - may retry
    except ApiError:
        # Response parsing failed - log for investigation
"""

from typing import Any


class ScraperError(Exception):
    """Base class for all scraper errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidEventIdError(ScraperError):
    """Event not found or invalid ID."""

    def __init__(self, event_id: str, message: str | None = None) -> None:
        self.event_id = event_id
        msg = message or f"Invalid or not found event: {event_id}"
        super().__init__(msg)


class NetworkError(ScraperError):
    """Connection or timeout failure."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(message)


class ApiError(ScraperError):
    """Unexpected response structure from API."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.details = details or {}
        super().__init__(message)


class RateLimitError(ScraperError):
    """Rate limited by API."""

    def __init__(self, message: str = "Rate limited by API") -> None:
        super().__init__(message)
