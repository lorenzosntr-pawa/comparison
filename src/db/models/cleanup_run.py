"""Cleanup run tracking model."""

from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class CleanupRun(Base):
    """Tracks cleanup execution history for audit and monitoring.

    Records when cleanup jobs run, what settings were used,
    and how many records were deleted from each table.
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
