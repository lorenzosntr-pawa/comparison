"""Pydantic schemas for API request/response models.

This module defines request and response schemas for:
- Health check endpoints (platform connectivity status)
- Scrape operations (trigger, status, errors)

All schemas use Pydantic for validation and serialization.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from src.scraping.schemas import Platform, PlatformResult


class PlatformHealth(BaseModel):
    """Health status for a single platform.

    Attributes:
        platform: Platform enum value (sportybet, betpawa, bet9ja).
        status: Current status ('healthy' or 'unhealthy').
        response_time_ms: Response time in milliseconds if available.
        error: Error message if platform is unhealthy.
    """

    platform: Platform
    status: str = Field(description="'healthy' or 'unhealthy'")
    response_time_ms: int | None = Field(
        default=None, description="Response time in milliseconds"
    )
    error: str | None = Field(default=None, description="Error message if unhealthy")


class HealthResponse(BaseModel):
    """Response from health check endpoint.

    Provides overall system health status based on database connectivity
    and platform reachability.

    Attributes:
        status: Overall status ('healthy', 'degraded', or 'unhealthy').
        database: Database connectivity status ('connected' or 'disconnected').
        platforms: Per-platform health details.
    """

    status: str = Field(
        description="'healthy' (all up), 'degraded' (some up), 'unhealthy' (none up)"
    )
    database: str = Field(description="'connected' or 'disconnected'")
    platforms: list[PlatformHealth] = Field(description="Per-platform health details")


class ScrapeRequest(BaseModel):
    """Request body for triggering a scrape operation.

    Allows optional filtering by platform, sport, or competition.
    All fields are optional - omitting them triggers a full scrape.

    Attributes:
        platforms: Optional list of platforms to scrape.
        sport_id: Optional sport ID filter (e.g., '2' for football).
        competition_id: Optional competition ID filter.
    """

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
    """Response from a scrape operation.

    Contains scrape run metadata, timing, per-platform results,
    and optional full event data.

    Attributes:
        scrape_run_id: Unique database ID for this scrape run.
        status: Overall status ('completed', 'partial', or 'failed').
        started_at: Timestamp when scrape started.
        completed_at: Timestamp when scrape finished.
        platforms: Per-platform result details.
        total_events: Sum of events scraped across all successful platforms.
        events: Full event data (only if detail=full was requested).
    """

    scrape_run_id: int = Field(
        description="Unique identifier for this scrape run"
    )
    status: str = Field(
        description="Overall status: 'completed', 'partial', or 'failed'"
    )
    started_at: datetime = Field(description="Timestamp when scrape started")
    completed_at: datetime = Field(description="Timestamp when scrape finished")
    platforms: list[PlatformResult] = Field(description="Per-platform results")
    total_events: int = Field(
        description="Sum of events scraped across all successful platforms"
    )
    events: list[dict] | None = Field(
        default=None,
        description="Full event data, only if detail=full",
    )


class ScrapeErrorResponse(BaseModel):
    """Error details for a scrape run.

    Captures individual errors that occurred during a scrape operation.

    Attributes:
        id: Error record database ID.
        error_type: Category of error (e.g., 'timeout', 'connection').
        error_message: Human-readable error description.
        occurred_at: Timestamp when error occurred.
        platform: Platform where error occurred, if applicable.
    """

    id: int = Field(description="Error record database ID")
    error_type: str = Field(description="Category of error")
    error_message: str = Field(description="Human-readable error description")
    occurred_at: datetime = Field(description="Timestamp when error occurred")
    platform: str | None = Field(default=None, description="Platform where error occurred")


class ScrapeStatusResponse(BaseModel):
    """Response for scrape run status check.

    Provides comprehensive status information for a scrape run including
    progress, timing, and any errors encountered.

    Attributes:
        scrape_run_id: Unique database ID for this scrape run.
        status: Current status ('running', 'completed', 'partial', or 'failed').
        started_at: Timestamp when scrape started.
        completed_at: Timestamp when scrape finished (None if still running).
        events_scraped: Number of events successfully scraped.
        events_failed: Number of events that failed to scrape.
        trigger: What triggered this run ('api', 'scheduler', 'retry:N').
        platforms: Per-platform result details if available.
        platform_timings: Per-platform timing breakdown.
        errors: List of errors that occurred during this run.
    """

    scrape_run_id: int = Field(description="Unique identifier for this scrape run")
    status: str = Field(
        description="Status: 'running', 'completed', 'partial', or 'failed'"
    )
    started_at: datetime = Field(description="Timestamp when scrape started")
    completed_at: datetime | None = Field(
        default=None, description="Timestamp when scrape finished"
    )
    events_scraped: int = Field(default=0, description="Events successfully scraped")
    events_failed: int = Field(default=0, description="Events that failed to scrape")
    trigger: str | None = Field(
        default=None, description="What triggered this run"
    )
    platforms: list[PlatformResult] | None = Field(
        default=None, description="Per-platform result details"
    )
    platform_timings: dict[str, dict] | None = Field(
        default=None,
        description="Per-platform timing: {platform: {duration_ms, events_count}}",
    )
    errors: list[ScrapeErrorResponse] | None = Field(
        default=None,
        description="List of errors that occurred during this run",
    )
