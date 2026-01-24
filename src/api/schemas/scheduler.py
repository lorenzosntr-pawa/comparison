"""Pydantic schemas for scheduler monitoring endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobStatus(BaseModel):
    """Status information for a scheduled job."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    next_run: datetime | None
    trigger_type: str
    interval_minutes: int | None


class SchedulerStatus(BaseModel):
    """Overall scheduler status with job list."""

    model_config = ConfigDict(from_attributes=True)

    running: bool
    paused: bool
    jobs: list[JobStatus]


class SchedulerPlatformHealth(BaseModel):
    """Health status for a platform based on scrape history."""

    model_config = ConfigDict(from_attributes=True)

    platform: str
    healthy: bool
    last_success: datetime | None


class RunHistoryEntry(BaseModel):
    """Single scrape run entry for history listing."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: datetime
    completed_at: datetime | None
    events_scraped: int
    events_failed: int
    trigger: str | None
    duration_seconds: float | None
    platform_timings: dict | None = None


class RunHistoryResponse(BaseModel):
    """Paginated response for scrape run history."""

    model_config = ConfigDict(from_attributes=True)

    runs: list[RunHistoryEntry]
    total: int


class ScrapePhaseLogResponse(BaseModel):
    """Single phase log entry for audit trail."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str | None
    phase: str
    started_at: datetime
    ended_at: datetime | None
    events_processed: int | None
    message: str | None


class ScrapeRunResponse(BaseModel):
    """Full scrape run details for list and detail endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: datetime
    completed_at: datetime | None
    events_scraped: int
    events_failed: int
    trigger: str | None
    platform_timings: dict | None = None
    phase_logs: list[ScrapePhaseLogResponse] | None = None  # Optional audit trail


class ScrapeStatsResponse(BaseModel):
    """Aggregate statistics for scrape runs."""

    total_runs: int
    runs_24h: int
    avg_duration_seconds: float | None


class DailyMetric(BaseModel):
    """Daily aggregated scrape metrics for analytics."""

    date: str  # YYYY-MM-DD
    avg_duration_seconds: float
    total_events: int
    success_count: int
    failure_count: int
    partial_count: int


class PlatformMetric(BaseModel):
    """Per-platform aggregated metrics for analytics."""

    platform: str
    success_rate: float  # 0-100
    avg_duration_seconds: float
    total_events: int


class ScrapeAnalyticsResponse(BaseModel):
    """Historical analytics response with daily and platform metrics."""

    daily_metrics: list[DailyMetric]
    platform_metrics: list[PlatformMetric]
    period_start: str
    period_end: str


class RetryRequest(BaseModel):
    """Request body for retrying failed platforms in a scrape run."""

    platforms: list[str] = []  # Empty list = retry all failed platforms


class RetryResponse(BaseModel):
    """Response from retry endpoint."""

    new_run_id: int
    platforms_retried: list[str]
    message: str


class PlatformDiscoveryResult(BaseModel):
    """Discovery results for a single platform."""

    new: int
    updated: int
    error: str | None = None


class TournamentDiscoveryResponse(BaseModel):
    """Response from tournament discovery endpoint."""

    sportybet: PlatformDiscoveryResult
    bet9ja: PlatformDiscoveryResult
    total_tournaments: int


class CompetitorScrapeResult(BaseModel):
    """Scrape results for a single competitor platform."""

    platform: str
    new_events: int
    updated_events: int
    snapshots: int
    markets: int
    events_with_full_odds: int = 0
    error: str | None = None


class CompetitorScrapeResponse(BaseModel):
    """Response from competitor event scraping endpoint."""

    sportybet: CompetitorScrapeResult
    bet9ja: CompetitorScrapeResult
    duration_ms: int
