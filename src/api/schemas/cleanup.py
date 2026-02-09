"""Pydantic schemas for cleanup API endpoints.

This module defines request and response schemas for the data cleanup system:
- Statistics about current data (DataStats, TableStats)
- Cleanup preview and execution (CleanupPreview, CleanupResult)
- Cleanup run history (CleanupRunResponse, CleanupHistoryResponse)
- Activity status (CleanupStatusResponse)

Uses camelCase aliases for frontend compatibility.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TableStats(BaseModel):
    """Statistics for a single database table.

    Attributes:
        count: Total number of records in the table.
        oldest: Timestamp of oldest record, if any.
        newest: Timestamp of newest record, if any.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    count: int = Field(description="Total number of records")
    oldest: datetime | None = Field(default=None, description="Oldest record timestamp")
    newest: datetime | None = Field(default=None, description="Newest record timestamp")


class PlatformCount(BaseModel):
    """Count breakdown by platform.

    Attributes:
        platform: Platform slug (e.g., 'betpawa', 'sportybet', 'bet9ja').
        count: Number of records for this platform.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    platform: str = Field(description="Platform slug identifier")
    count: int = Field(description="Number of records")


class DataStats(BaseModel):
    """Overall data statistics for cleanup preview.

    Comprehensive statistics across all major tables, used to show
    current data state before cleanup.

    Attributes:
        odds_snapshots: Stats for BetPawa odds snapshots.
        competitor_odds_snapshots: Stats for competitor odds snapshots.
        events: Stats for BetPawa events.
        competitor_events: Stats for competitor events.
        tournaments: Stats for BetPawa tournaments.
        competitor_tournaments: Stats for competitor tournaments.
        scrape_runs: Stats for scrape run records.
        scrape_batches: Stats for scrape batch records.
        events_by_platform: Event count breakdown by platform.
        competitor_events_by_source: Competitor event breakdown by source.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    odds_snapshots: TableStats = Field(description="BetPawa odds snapshot stats")
    competitor_odds_snapshots: TableStats = Field(description="Competitor odds stats")
    events: TableStats = Field(description="BetPawa event stats")
    competitor_events: TableStats = Field(description="Competitor event stats")
    tournaments: TableStats = Field(description="BetPawa tournament stats")
    competitor_tournaments: TableStats = Field(description="Competitor tournament stats")
    scrape_runs: TableStats = Field(description="Scrape run record stats")
    scrape_batches: TableStats = Field(description="Scrape batch record stats")

    # Breakdown by platform
    events_by_platform: list[PlatformCount] = Field(
        default=[], description="Event count by platform"
    )
    competitor_events_by_source: list[PlatformCount] = Field(
        default=[], description="Competitor event count by source"
    )


class CleanupPreview(BaseModel):
    """Preview of what would be deleted by cleanup.

    Shows cutoff dates and record counts that would be affected by
    running cleanup with the current retention settings.

    Attributes:
        odds_cutoff_date: Records older than this will be deleted.
        match_cutoff_date: Match records older than this will be deleted.
        odds_snapshots_count: BetPawa odds snapshots to delete.
        competitor_odds_snapshots_count: Competitor odds snapshots to delete.
        scrape_runs_count: Scrape run records to delete.
        scrape_batches_count: Scrape batch records to delete.
        events_count: BetPawa events to delete.
        competitor_events_count: Competitor events to delete.
        tournaments_count: BetPawa tournaments to delete.
        competitor_tournaments_count: Competitor tournaments to delete.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    odds_cutoff_date: datetime = Field(description="Odds older than this will be deleted")
    match_cutoff_date: datetime = Field(description="Matches older than this will be deleted")

    # Counts to be deleted
    odds_snapshots_count: int = Field(description="BetPawa odds snapshots to delete")
    competitor_odds_snapshots_count: int = Field(description="Competitor odds to delete")
    scrape_runs_count: int = Field(description="Scrape runs to delete")
    scrape_batches_count: int = Field(description="Scrape batches to delete")
    events_count: int = Field(description="BetPawa events to delete")
    competitor_events_count: int = Field(description="Competitor events to delete")
    tournaments_count: int = Field(description="BetPawa tournaments to delete")
    competitor_tournaments_count: int = Field(description="Competitor tournaments to delete")


class CleanupResult(BaseModel):
    """Result of cleanup execution.

    Contains counts of records deleted and timing information.

    Attributes:
        odds_deleted: Number of BetPawa odds snapshots deleted.
        competitor_odds_deleted: Number of competitor odds snapshots deleted.
        scrape_runs_deleted: Number of scrape runs deleted.
        scrape_batches_deleted: Number of scrape batches deleted.
        events_deleted: Number of BetPawa events deleted.
        competitor_events_deleted: Number of competitor events deleted.
        tournaments_deleted: Number of BetPawa tournaments deleted.
        competitor_tournaments_deleted: Number of competitor tournaments deleted.
        oldest_odds_date: Date of oldest odds record deleted.
        oldest_match_date: Date of oldest match record deleted.
        duration_seconds: Time taken to execute cleanup.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    odds_deleted: int = Field(description="BetPawa odds snapshots deleted")
    competitor_odds_deleted: int = Field(description="Competitor odds deleted")
    scrape_runs_deleted: int = Field(description="Scrape runs deleted")
    scrape_batches_deleted: int = Field(description="Scrape batches deleted")
    events_deleted: int = Field(description="BetPawa events deleted")
    competitor_events_deleted: int = Field(description="Competitor events deleted")
    tournaments_deleted: int = Field(description="BetPawa tournaments deleted")
    competitor_tournaments_deleted: int = Field(description="Competitor tournaments deleted")

    # Date ranges cleaned
    oldest_odds_date: datetime | None = Field(
        default=None, description="Oldest odds record deleted"
    )
    oldest_match_date: datetime | None = Field(
        default=None, description="Oldest match record deleted"
    )

    duration_seconds: float = Field(description="Time taken to execute cleanup")


class CleanupExecuteRequest(BaseModel):
    """Request body for manual cleanup execution.

    Optional parameters to override default retention settings.

    Attributes:
        odds_retention_days: Days of odds to retain (overrides settings).
        match_retention_days: Days of matches to retain (overrides settings).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    odds_retention_days: int | None = Field(
        default=None, description="Days of odds data to retain"
    )
    match_retention_days: int | None = Field(
        default=None, description="Days of match data to retain"
    )


class CleanupRunResponse(BaseModel):
    """Response model for a single cleanup run record.

    Complete record of a cleanup execution including configuration,
    results, timing, and any errors.

    Attributes:
        id: Unique database ID.
        started_at: When cleanup started.
        completed_at: When cleanup finished.
        trigger: What triggered the run ('manual' or 'scheduled').
        odds_retention_days: Retention setting used for odds.
        match_retention_days: Retention setting used for matches.
        odds_deleted: BetPawa odds snapshots deleted.
        competitor_odds_deleted: Competitor odds deleted.
        scrape_runs_deleted: Scrape runs deleted.
        scrape_batches_deleted: Scrape batches deleted.
        events_deleted: BetPawa events deleted.
        competitor_events_deleted: Competitor events deleted.
        tournaments_deleted: BetPawa tournaments deleted.
        competitor_tournaments_deleted: Competitor tournaments deleted.
        oldest_odds_date: Oldest odds record date deleted.
        oldest_match_date: Oldest match record date deleted.
        status: Run status ('completed', 'failed').
        error_message: Error details if failed.
        duration_seconds: Execution time.
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int = Field(description="Unique database ID")
    started_at: datetime = Field(description="When cleanup started")
    completed_at: datetime | None = Field(default=None, description="When cleanup finished")
    trigger: str = Field(description="What triggered the run")
    odds_retention_days: int = Field(description="Retention setting for odds")
    match_retention_days: int = Field(description="Retention setting for matches")
    odds_deleted: int = Field(description="BetPawa odds deleted")
    competitor_odds_deleted: int = Field(description="Competitor odds deleted")
    scrape_runs_deleted: int = Field(description="Scrape runs deleted")
    scrape_batches_deleted: int = Field(description="Scrape batches deleted")
    events_deleted: int = Field(description="BetPawa events deleted")
    competitor_events_deleted: int = Field(description="Competitor events deleted")
    tournaments_deleted: int = Field(description="BetPawa tournaments deleted")
    competitor_tournaments_deleted: int = Field(description="Competitor tournaments deleted")
    oldest_odds_date: datetime | None = Field(default=None, description="Oldest odds date")
    oldest_match_date: datetime | None = Field(default=None, description="Oldest match date")
    status: str = Field(description="Run status")
    error_message: str | None = Field(default=None, description="Error details if failed")
    duration_seconds: float | None = Field(default=None, description="Execution time")


class CleanupHistoryResponse(BaseModel):
    """Response model for cleanup history list.

    Attributes:
        runs: List of cleanup run records.
        total: Total number of cleanup runs in database.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    runs: list[CleanupRunResponse] = Field(description="Cleanup run records")
    total: int = Field(description="Total cleanup runs in database")


class CleanupStatusResponse(BaseModel):
    """Response model for cleanup/scraping activity status.

    Used by frontend to show activity indicators and prevent
    conflicting operations.

    Attributes:
        is_cleanup_running: Whether cleanup is currently in progress.
        is_scraping_active: Whether a scrape is currently in progress.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    is_cleanup_running: bool = Field(description="Cleanup is in progress")
    is_scraping_active: bool = Field(description="Scrape is in progress")
