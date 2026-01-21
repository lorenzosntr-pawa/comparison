"""Pydantic schemas for API request/response models."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.scraping.schemas import Platform, PlatformResult


class PlatformHealth(BaseModel):
    """Health status for a single platform."""

    platform: Platform
    status: str = Field(description="'healthy' or 'unhealthy'")
    response_time_ms: int | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Response from health check endpoint."""

    status: str = Field(
        description="'healthy' (all up), 'degraded' (some up), 'unhealthy' (none up)"
    )
    database: str = Field(description="'connected' or 'disconnected'")
    platforms: list[PlatformHealth]


class ScrapeRequest(BaseModel):
    """Request body for triggering a scrape operation."""

    platforms: list[Platform] | None = Field(
        default=None,
        description="Platforms to scrape. Default: all three",
    )
    sport_id: str | None = Field(
        default=None,
        description="Filter by sport ID (e.g., '2' for football)",
    )
    competition_id: str | None = Field(
        default=None,
        description="Filter by specific competition",
    )


class ScrapeResponse(BaseModel):
    """Response from a scrape operation."""

    scrape_run_id: int = Field(
        description="Unique identifier for this scrape run (0 until DB integration)"
    )
    status: str = Field(
        description="Overall status: 'completed', 'partial', or 'failed'"
    )
    started_at: datetime
    completed_at: datetime
    platforms: list[PlatformResult]
    total_events: int = Field(
        description="Sum of events scraped across all successful platforms"
    )
    events: list[dict] | None = Field(
        default=None,
        description="Full event data, only if detail=full",
    )


class ScrapeErrorResponse(BaseModel):
    """Error details for a scrape run."""

    id: int
    error_type: str
    error_message: str
    occurred_at: datetime
    platform: str | None = None


class ScrapeStatusResponse(BaseModel):
    """Response for scrape run status check."""

    scrape_run_id: int
    status: str = Field(
        description="Status: 'running', 'completed', 'partial', or 'failed'"
    )
    started_at: datetime
    completed_at: datetime | None = None
    events_scraped: int = 0
    events_failed: int = 0
    trigger: str | None = None
    platforms: list[PlatformResult] | None = None
    platform_timings: dict[str, dict] | None = Field(
        default=None,
        description="Per-platform timing: {platform: {duration_ms, events_count}}",
    )
    errors: list[ScrapeErrorResponse] | None = Field(
        default=None,
        description="List of errors that occurred during this run",
    )
