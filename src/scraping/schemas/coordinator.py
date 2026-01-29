"""Coordinator-specific data structures for event-centric scraping.

This module defines the core data structures used by EventCoordinator:
- ScrapeStatus: Enum for tracking event scrape lifecycle
- EventTarget: Dataclass representing an event to scrape across platforms
- ScrapeBatch: TypedDict for a batch of events to process together
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import TypedDict


class ScrapeStatus(StrEnum):
    """Status of an event in the scrape cycle.

    Uses StrEnum for DB compatibility - values serialize as strings.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EventTarget:
    """Represents a single event to scrape across platforms.

    This is a mutable dataclass (not Pydantic) because the status and results
    are updated during the scrape cycle.

    Attributes:
        sr_id: SportRadar ID (unique identifier across platforms).
        kickoff: Event start time (UTC).
        platforms: Set of bookmakers where this event is available.
        platform_ids: Maps platform name to platform-specific event ID for API calls.
        status: Current scrape status.
        results: Scraped data per platform (None if not yet scraped).
        errors: Error messages per platform (if any failures).
    """

    sr_id: str
    kickoff: datetime
    platforms: set[str] = field(default_factory=set)
    platform_ids: dict[str, str] = field(default_factory=dict)
    status: ScrapeStatus = ScrapeStatus.PENDING
    results: dict[str, dict | None] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def coverage_count(self) -> int:
        """Number of platforms where this event is available."""
        return len(self.platforms)

    @property
    def has_betpawa(self) -> bool:
        """Whether this event is available on BetPawa (primary platform)."""
        return "betpawa" in self.platforms

    def priority_key(self) -> tuple:
        """Generate a comparable tuple for priority queue ordering.

        Lower values = higher priority for min-heap.

        Priority ordering:
        1. Urgency tier based on kickoff time (imminent > soon > future)
        2. Kickoff time (earlier = higher priority)
        3. Coverage count (more platforms = higher priority, so negated)
        4. BetPawa presence (has BetPawa = higher priority, so negated)

        Returns:
            Tuple for comparison: (urgency, kickoff, -coverage, not_has_betpawa)
        """
        now = datetime.now(timezone.utc)

        # Handle both tz-aware and naive datetimes
        kickoff_utc = self.kickoff
        if kickoff_utc.tzinfo is None:
            kickoff_utc = kickoff_utc.replace(tzinfo=timezone.utc)

        minutes_until = (kickoff_utc - now).total_seconds() / 60

        # Urgency tier (0 = imminent, 1 = soon, 2 = future)
        if minutes_until < 30:
            urgency = 0
        elif minutes_until < 120:
            urgency = 1
        else:
            urgency = 2

        return (
            urgency,
            self.kickoff,
            -self.coverage_count,  # More coverage = higher priority
            not self.has_betpawa,  # BetPawa presence = higher priority
        )


class ScrapeBatch(TypedDict):
    """A batch of events to scrape together.

    Uses TypedDict for simple dict structure with type hints.
    """

    batch_id: str
    events: list[EventTarget]
    created_at: datetime
