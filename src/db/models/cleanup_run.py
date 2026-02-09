"""Cleanup run tracking model.

This module defines the CleanupRun model for tracking data retention
operations. Cleanup jobs delete old odds snapshots and expired events
to manage database size.
"""

from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class CleanupRun(Base):
    """Tracks cleanup execution history for audit and monitoring.

    Records when cleanup jobs run, what retention settings were applied,
    and how many records were deleted from each table. Used for operational
    visibility and debugging of data retention policies.

    Attributes:
        id: Primary key.
        started_at: When the cleanup job started.
        completed_at: When the job finished (null if still running/failed).
        trigger: How the cleanup was initiated ("scheduled" or "manual").
        odds_retention_days: Retention policy used for odds data.
        match_retention_days: Retention policy used for match data.
        odds_deleted: Count of odds_snapshots rows deleted.
        competitor_odds_deleted: Count of competitor_odds_snapshots deleted.
        scrape_runs_deleted: Count of scrape_runs rows deleted.
        scrape_batches_deleted: Count of scrape_batches rows deleted.
        events_deleted: Count of events rows deleted.
        competitor_events_deleted: Count of competitor_events deleted.
        tournaments_deleted: Count of tournaments rows deleted.
        competitor_tournaments_deleted: Count of competitor_tournaments deleted.
        oldest_odds_date: Oldest odds timestamp that was cleaned.
        oldest_match_date: Oldest match timestamp that was cleaned.
        status: Current status ("running", "completed", "failed").
        error_message: Error details if status is "failed".
        duration_seconds: Total execution time.
    """

    __tablename__ = "cleanup_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    trigger: Mapped[str] = mapped_column(String(20))  # "scheduled" or "manual"

    # Settings used for this cleanup
    odds_retention_days: Mapped[int]
    match_retention_days: Mapped[int]

    # Deletion counts per table
    odds_deleted: Mapped[int] = mapped_column(default=0)
    competitor_odds_deleted: Mapped[int] = mapped_column(default=0)
    scrape_runs_deleted: Mapped[int] = mapped_column(default=0)
    scrape_batches_deleted: Mapped[int] = mapped_column(default=0)
    events_deleted: Mapped[int] = mapped_column(default=0)
    competitor_events_deleted: Mapped[int] = mapped_column(default=0)
    tournaments_deleted: Mapped[int] = mapped_column(default=0)
    competitor_tournaments_deleted: Mapped[int] = mapped_column(default=0)

    # Date range that was cleaned
    oldest_odds_date: Mapped[datetime | None] = mapped_column(nullable=True)
    oldest_match_date: Mapped[datetime | None] = mapped_column(nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="running")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
