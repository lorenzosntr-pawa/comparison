"""Pydantic schemas for scraping orchestration."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Platform(StrEnum):
    """Supported betting platforms."""

    SPORTYBET = "sportybet"
    BETPAWA = "betpawa"
    BET9JA = "bet9ja"


class PlatformResult(BaseModel):
    """Result from scraping a single platform."""

    platform: Platform
    success: bool
    events_count: int = 0
    error_message: str | None = None
    duration_ms: int
    events: list[dict] | None = Field(
        default=None,
        description="Raw events if include_data=True",
    )


class ScrapeResult(BaseModel):
    """Aggregated result from scraping all platforms."""

    status: str = Field(
        description="Overall status: 'completed' (all success), 'partial' (some), 'failed' (none)"
    )
    started_at: datetime
    completed_at: datetime
    platforms: list[PlatformResult]
    total_events: int = Field(
        description="Sum of events_count across successful platforms"
    )


class ScrapeProgress(BaseModel):
    """Progress update during scraping."""

    platform: Platform | None = None  # None for overall updates
    phase: str  # "starting", "scraping", "storing", "completed", "failed"
    current: int  # Current platform index (0-based)
    total: int  # Total platforms
    events_count: int | None = None  # Events scraped so far for this platform
    duration_ms: int | None = None  # Duration in ms (set on platform completion)
    message: str | None = None  # Human-readable status message
    timestamp: datetime = Field(default_factory=datetime.utcnow)
