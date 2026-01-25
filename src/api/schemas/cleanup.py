"""Pydantic schemas for cleanup API endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class TableStats(BaseModel):
    """Stats for a single table."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    count: int
    oldest: datetime | None = None
    newest: datetime | None = None


class PlatformCount(BaseModel):
    """Count breakdown by platform."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    platform: str
    count: int


class DataStats(BaseModel):
    """Overall data statistics for cleanup preview."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    odds_snapshots: TableStats
    competitor_odds_snapshots: TableStats
    events: TableStats
    competitor_events: TableStats
    tournaments: TableStats
    competitor_tournaments: TableStats
    scrape_runs: TableStats
    scrape_batches: TableStats

    # Breakdown by platform
    events_by_platform: list[PlatformCount] = []
    competitor_events_by_source: list[PlatformCount] = []


class CleanupPreview(BaseModel):
    """Preview of what would be deleted by cleanup."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    odds_cutoff_date: datetime
    match_cutoff_date: datetime

    # Counts to be deleted
    odds_snapshots_count: int
    competitor_odds_snapshots_count: int
    scrape_runs_count: int
    scrape_batches_count: int
    events_count: int
    competitor_events_count: int
    tournaments_count: int
    competitor_tournaments_count: int


class CleanupResult(BaseModel):
    """Result of cleanup execution."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    odds_deleted: int
    competitor_odds_deleted: int
    scrape_runs_deleted: int
    scrape_batches_deleted: int
    events_deleted: int
    competitor_events_deleted: int
    tournaments_deleted: int
    competitor_tournaments_deleted: int

    # Date ranges cleaned
    oldest_odds_date: datetime | None = None
    oldest_match_date: datetime | None = None

    duration_seconds: float
