"""Pydantic schemas for scraping orchestration."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Platform(StrEnum):
    """Supported betting platforms."""

    BETPAWA = "betpawa"  # Must be first - canonical source for SportRadar IDs
    SPORTYBET = "sportybet"
    BET9JA = "bet9ja"


class ScrapePhase(StrEnum):
    """Phases of a scrape workflow execution.

    Provides type-safe phase tracking throughout the scraping lifecycle.
    """

    INITIALIZING = "initializing"
    DISCOVERING = "discovering"
    SCRAPING = "scraping"
    MAPPING = "mapping"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlatformStatus(StrEnum):
    """Status of an individual platform within a scrape run.

    Tracks per-platform progress during parallel scraping operations.
    """

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


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


class ScrapeErrorContext(BaseModel):
    """Structured error context for scrape failures."""

    error_type: str  # e.g., "timeout", "network", "parse", "storage"
    error_message: str
    platform: str | None = None
    recoverable: bool = False


class ScrapeProgress(BaseModel):
    """Progress update during scraping."""

    platform: Platform | None = None  # None for overall updates
    phase: ScrapePhase | str  # ScrapePhase enum (serializes to string for SSE compat)
    current: int  # Current platform index (0-based)
    total: int  # Total platforms
    events_count: int | None = None  # Events scraped so far for this platform
    duration_ms: int | None = None  # Duration in ms (set on platform completion)
    message: str | None = None  # Human-readable status message
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    scrape_run_id: int | None = None  # Track which run this progress belongs to
    elapsed_ms: int | None = None  # Time since platform start
    error: ScrapeErrorContext | None = None  # Structured error info
