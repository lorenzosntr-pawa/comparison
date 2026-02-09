"""Pydantic schemas for scheduler monitoring endpoints.

This module defines schemas for scheduler status, run history,
analytics, and platform health. Used by scheduler monitoring
and scrape operation endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(BaseModel):
    """Status information for a scheduled job.

    Attributes:
        id: Unique job identifier.
        next_run: Scheduled next execution time.
        trigger_type: Type of trigger (e.g., 'IntervalTrigger').
        interval_minutes: Interval in minutes for recurring jobs.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Unique job identifier")
    next_run: datetime | None = Field(description="Next scheduled execution")
    trigger_type: str = Field(description="Type of trigger")
    interval_minutes: int | None = Field(description="Interval in minutes")


class SchedulerStatus(BaseModel):
    """Overall scheduler status with job list.

    Attributes:
        running: Whether the scheduler is running.
        paused: Whether the scheduler is paused (jobs won't execute).
        jobs: List of scheduled job statuses.
    """

    model_config = ConfigDict(from_attributes=True)

    running: bool = Field(description="Scheduler is running")
    paused: bool = Field(description="Scheduler is paused")
    jobs: list[JobStatus] = Field(description="Scheduled job statuses")


class SchedulerPlatformHealth(BaseModel):
    """Health status for a platform based on scrape history.

    Attributes:
        platform: Platform slug identifier.
        healthy: Whether recent scrapes succeeded.
        last_success: Timestamp of last successful scrape.
    """

    model_config = ConfigDict(from_attributes=True)

    platform: str = Field(description="Platform slug identifier")
    healthy: bool = Field(description="Recent scrapes succeeded")
    last_success: datetime | None = Field(description="Last successful scrape time")


class RunHistoryEntry(BaseModel):
    """Single scrape run entry for history listing.

    Attributes:
        id: Unique database ID.
        status: Run status (running, completed, partial, failed).
        started_at: When the run started.
        completed_at: When the run finished.
        events_scraped: Successfully scraped event count.
        events_failed: Failed event count.
        trigger: What triggered the run (api, scheduler, retry).
        duration_seconds: Total run duration.
        platform_timings: Per-platform timing breakdown.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique database ID")
    status: str = Field(description="Run status")
    started_at: datetime = Field(description="When run started")
    completed_at: datetime | None = Field(description="When run finished")
    events_scraped: int = Field(description="Events successfully scraped")
    events_failed: int = Field(description="Events that failed")
    trigger: str | None = Field(description="What triggered the run")
    duration_seconds: float | None = Field(description="Total run duration")
    platform_timings: dict | None = Field(default=None, description="Per-platform timing")


class RunHistoryResponse(BaseModel):
    """Paginated response for scrape run history.

    Attributes:
        runs: List of run history entries.
        total: Total number of runs in database.
    """

    model_config = ConfigDict(from_attributes=True)

    runs: list[RunHistoryEntry] = Field(description="Run history entries")
    total: int = Field(description="Total runs in database")


class ScrapePhaseLogResponse(BaseModel):
    """Single phase log entry for audit trail.

    Tracks phase transitions during a scrape run for debugging
    and timeline visualization.

    Attributes:
        id: Unique database ID.
        platform: Platform this phase relates to.
        phase: Phase name (e.g., 'discovery', 'scraping', 'matching').
        started_at: When phase started.
        ended_at: When phase ended.
        events_processed: Number of events processed in this phase.
        message: Additional context or status message.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique database ID")
    platform: str | None = Field(description="Related platform")
    phase: str = Field(description="Phase name")
    started_at: datetime = Field(description="When phase started")
    ended_at: datetime | None = Field(description="When phase ended")
    events_processed: int | None = Field(description="Events processed")
    message: str | None = Field(description="Status message")


class ScrapeRunResponse(BaseModel):
    """Full scrape run details for list and detail endpoints.

    Comprehensive scrape run information including timing,
    event counts, and optional phase audit trail.

    Attributes:
        id: Unique database ID.
        status: Run status (running, completed, partial, failed).
        started_at: When the run started.
        completed_at: When the run finished.
        events_scraped: Successfully scraped event count.
        events_failed: Failed event count.
        trigger: What triggered the run.
        platform_timings: Per-platform timing breakdown.
        phase_logs: Optional phase transition audit trail.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unique database ID")
    status: str = Field(description="Run status")
    started_at: datetime = Field(description="When run started")
    completed_at: datetime | None = Field(description="When run finished")
    events_scraped: int = Field(description="Events successfully scraped")
    events_failed: int = Field(description="Events that failed")
    trigger: str | None = Field(description="What triggered the run")
    platform_timings: dict | None = Field(default=None, description="Per-platform timing")
    phase_logs: list[ScrapePhaseLogResponse] | None = Field(
        default=None, description="Phase transition audit trail"
    )


class ScrapeStatsResponse(BaseModel):
    """Aggregate statistics for scrape runs.

    Attributes:
        total_runs: Total number of scrape runs in database.
        runs_24h: Number of runs in last 24 hours.
        avg_duration_seconds: Average run duration (completed runs only).
    """

    total_runs: int = Field(description="Total scrape runs in database")
    runs_24h: int = Field(description="Runs in last 24 hours")
    avg_duration_seconds: float | None = Field(description="Average run duration")


class DailyMetric(BaseModel):
    """Daily aggregated scrape metrics for analytics.

    Attributes:
        date: Date in YYYY-MM-DD format.
        avg_duration_seconds: Average run duration for the day.
        total_events: Total events scraped.
        success_count: Number of fully successful runs.
        failure_count: Number of failed runs.
        partial_count: Number of partially successful runs.
    """

    date: str = Field(description="Date (YYYY-MM-DD)")
    avg_duration_seconds: float = Field(description="Average run duration")
    total_events: int = Field(description="Total events scraped")
    success_count: int = Field(description="Fully successful runs")
    failure_count: int = Field(description="Failed runs")
    partial_count: int = Field(description="Partially successful runs")


class PlatformMetric(BaseModel):
    """Per-platform aggregated metrics for analytics.

    Attributes:
        platform: Platform slug identifier.
        success_rate: Percentage of successful scrapes (0-100).
        avg_duration_seconds: Average scrape duration for this platform.
        total_events: Total events scraped from this platform.
    """

    platform: str = Field(description="Platform slug")
    success_rate: float = Field(description="Success rate percentage (0-100)")
    avg_duration_seconds: float = Field(description="Average scrape duration")
    total_events: int = Field(description="Total events scraped")


class ScrapeAnalyticsResponse(BaseModel):
    """Historical analytics response with daily and platform metrics.

    Attributes:
        daily_metrics: Aggregated metrics per day.
        platform_metrics: Aggregated metrics per platform.
        period_start: Start date of analysis period (YYYY-MM-DD).
        period_end: End date of analysis period (YYYY-MM-DD).
    """

    daily_metrics: list[DailyMetric] = Field(description="Metrics per day")
    platform_metrics: list[PlatformMetric] = Field(description="Metrics per platform")
    period_start: str = Field(description="Analysis period start (YYYY-MM-DD)")
    period_end: str = Field(description="Analysis period end (YYYY-MM-DD)")


class RetryRequest(BaseModel):
    """Request body for retrying failed platforms in a scrape run.

    Attributes:
        platforms: Platforms to retry. Empty list retries all failed platforms.
    """

    platforms: list[str] = Field(
        default=[], description="Platforms to retry (empty = all failed)"
    )


class RetryResponse(BaseModel):
    """Response from retry endpoint.

    Attributes:
        new_run_id: Database ID of the new retry run.
        platforms_retried: List of platforms that were retried.
        message: Human-readable status message.
    """

    new_run_id: int = Field(description="New retry run database ID")
    platforms_retried: list[str] = Field(description="Platforms that were retried")
    message: str = Field(description="Status message")


class PlatformDiscoveryResult(BaseModel):
    """Discovery results for a single platform.

    Attributes:
        new: Number of newly discovered tournaments.
        updated: Number of existing tournaments updated.
        error: Error message if discovery failed.
    """

    new: int = Field(description="Newly discovered tournaments")
    updated: int = Field(description="Existing tournaments updated")
    error: str | None = Field(default=None, description="Error if discovery failed")


class TournamentDiscoveryResponse(BaseModel):
    """Response from tournament discovery endpoint.

    Attributes:
        sportybet: SportyBet discovery results.
        bet9ja: Bet9ja discovery results.
        total_tournaments: Total tournaments after discovery.
    """

    sportybet: PlatformDiscoveryResult = Field(description="SportyBet results")
    bet9ja: PlatformDiscoveryResult = Field(description="Bet9ja results")
    total_tournaments: int = Field(description="Total tournaments after discovery")


class CompetitorScrapeResult(BaseModel):
    """Scrape results for a single competitor platform.

    Attributes:
        platform: Platform slug identifier.
        new_events: Number of new events discovered.
        updated_events: Number of existing events updated.
        snapshots: Number of odds snapshots created.
        markets: Number of markets scraped.
        events_with_full_odds: Events with complete odds data.
        error: Error message if scrape failed.
    """

    platform: str = Field(description="Platform slug")
    new_events: int = Field(description="New events discovered")
    updated_events: int = Field(description="Existing events updated")
    snapshots: int = Field(description="Odds snapshots created")
    markets: int = Field(description="Markets scraped")
    events_with_full_odds: int = Field(default=0, description="Events with full odds")
    error: str | None = Field(default=None, description="Error if scrape failed")


class CompetitorScrapeResponse(BaseModel):
    """Response from competitor event scraping endpoint.

    Attributes:
        sportybet: SportyBet scrape results.
        bet9ja: Bet9ja scrape results.
        duration_ms: Total scrape duration in milliseconds.
    """

    sportybet: CompetitorScrapeResult = Field(description="SportyBet results")
    bet9ja: CompetitorScrapeResult = Field(description="Bet9ja results")
    duration_ms: int = Field(description="Total duration in milliseconds")


class EventMetricsByPlatform(BaseModel):
    """Per-platform metrics from EventScrapeStatus.

    Attributes:
        platform: Platform slug identifier.
        total_requested: Total event requests to this platform.
        total_scraped: Successfully scraped events.
        total_failed: Failed event scrapes.
        success_rate: Success percentage (0-100).
        avg_timing_ms: Average scrape timing in milliseconds.
    """

    platform: str = Field(description="Platform slug")
    total_requested: int = Field(description="Total event requests")
    total_scraped: int = Field(description="Successfully scraped")
    total_failed: int = Field(description="Failed scrapes")
    success_rate: float = Field(description="Success percentage (0-100)")
    avg_timing_ms: float = Field(description="Average timing in ms")


class EventScrapeMetricsResponse(BaseModel):
    """Response for event-level scrape metrics from EventCoordinator flow.

    Provides per-event success rates and platform performance insights.

    Attributes:
        period_start: Analysis period start (YYYY-MM-DD).
        period_end: Analysis period end (YYYY-MM-DD).
        total_events: Total events processed.
        events_fully_scraped: Events with all platforms successful.
        events_partially_scraped: Events with some platforms successful.
        events_failed: Events with no platforms successful.
        platform_metrics: Per-platform breakdown.
    """

    period_start: str = Field(description="Period start (YYYY-MM-DD)")
    period_end: str = Field(description="Period end (YYYY-MM-DD)")
    total_events: int = Field(description="Total events processed")
    events_fully_scraped: int = Field(description="All platforms succeeded")
    events_partially_scraped: int = Field(description="Some platforms succeeded")
    events_failed: int = Field(description="No platforms succeeded")
    platform_metrics: list[EventMetricsByPlatform] = Field(description="Per-platform metrics")


class SingleEventPlatformResult(BaseModel):
    """Per-platform result for single-event on-demand scrape.

    Attributes:
        platform: Platform slug identifier.
        success: Whether scrape succeeded.
        timing_ms: Scrape duration in milliseconds.
        error: Error message if failed.
        markets_count: Number of markets scraped.
    """

    model_config = ConfigDict(from_attributes=True)

    platform: str = Field(description="Platform slug")
    success: bool = Field(description="Whether scrape succeeded")
    timing_ms: int | None = Field(default=None, description="Duration in ms")
    error: str | None = Field(default=None, description="Error if failed")
    markets_count: int | None = Field(default=None, description="Markets scraped")


class SingleEventScrapeResponse(BaseModel):
    """Response from single-event on-demand scrape endpoint.

    Used by POST /api/scrape/event/{sr_id} for on-demand event refresh.

    Attributes:
        sportradar_id: SportRadar event ID that was scraped.
        status: Overall status (completed, partial, failed).
        platforms_scraped: List of platforms that succeeded.
        platforms_failed: List of platforms that failed.
        platform_results: Detailed per-platform results.
        total_timing_ms: Total scrape duration in milliseconds.
    """

    model_config = ConfigDict(from_attributes=True)

    sportradar_id: str = Field(description="SportRadar event ID")
    status: str = Field(description="Status: completed, partial, or failed")
    platforms_scraped: list[str] = Field(description="Successful platforms")
    platforms_failed: list[str] = Field(description="Failed platforms")
    platform_results: list[SingleEventPlatformResult] = Field(description="Per-platform details")
    total_timing_ms: int = Field(description="Total duration in ms")
