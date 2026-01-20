"""Exception hierarchy for scraper clients."""

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
