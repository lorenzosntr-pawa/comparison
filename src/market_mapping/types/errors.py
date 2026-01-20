"""Error Types for Market Mapping.

Provides structured error handling for mapping failures. These types
enable detailed feedback about why a mapping failed, making debugging
easier and providing actionable error messages to consumers.
"""

from enum import StrEnum
from typing import Any


class MappingErrorCode(StrEnum):
    """Error codes for mapping failures.

    Each code represents a specific failure type, allowing consumers
    to programmatically handle different error conditions.
    """

    UNKNOWN_MARKET = "UNKNOWN_MARKET"
    """No mapping exists for the market ID/key."""

    UNSUPPORTED_PLATFORM = "UNSUPPORTED_PLATFORM"
    """Market exists but not on Betpawa (betpawaId null)."""

    INVALID_SPECIFIER = "INVALID_SPECIFIER"
    """Specifier present but couldn't be parsed."""

    UNKNOWN_PARAM_MARKET = "UNKNOWN_PARAM_MARKET"
    """Parameterized market type not recognized."""

    NO_MATCHING_OUTCOMES = "NO_MATCHING_OUTCOMES"
    """All outcomes failed to map."""

    INVALID_ODDS = "INVALID_ODDS"
    """Odds value could not be parsed."""

    INVALID_KEY_FORMAT = "INVALID_KEY_FORMAT"
    """Bet9ja key format invalid."""


class MappingError(Exception):
    """Structured mapping error with code and context.

    Provides machine-readable error code, human-readable message,
    and optional context for debugging.

    Attributes:
        code: Machine-readable error code from MappingErrorCode enum.
        message: Human-readable error description.
        context: Optional debug context (marketId, specifier, key, etc.).

    Example:
        >>> raise MappingError(
        ...     code=MappingErrorCode.UNKNOWN_MARKET,
        ...     message="No mapping found for market ID '999'",
        ...     context={"market_id": "999"}
        ... )
    """

    def __init__(
        self,
        code: MappingErrorCode,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a MappingError.

        Args:
            code: Error code from MappingErrorCode enum.
            message: Human-readable error description.
            context: Optional debug context dictionary.
        """
        self.code = code
        self.message = message
        self.context = context
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message for display."""
        base = f"[{self.code}] {self.message}"
        if self.context:
            context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{base} ({context_str})"
        return base

    def __str__(self) -> str:
        """Return a formatted string representation of the error."""
        return self._format_message()

    def __repr__(self) -> str:
        """Return a detailed representation of the error."""
        return (
            f"MappingError(code={self.code!r}, "
            f"message={self.message!r}, "
            f"context={self.context!r})"
        )
