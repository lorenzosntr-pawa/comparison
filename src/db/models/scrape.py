"""Scrape run and error tracking models."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.bookmaker import Bookmaker
    from src.db.models.event import Event
    from src.db.models.odds import OddsSnapshot


class ScrapeStatus(StrEnum):
    """Status of a scrape run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some bookmakers succeeded, some failed
    FAILED = "failed"


class ScrapeRun(Base):
    """Tracks each scraping execution for operational monitoring."""

    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[ScrapeStatus] = mapped_column(
        String(20), default=ScrapeStatus.PENDING
    )
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    events_scraped: Mapped[int] = mapped_column(default=0)
    events_failed: Mapped[int] = mapped_column(default=0)
    trigger: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g., "scheduled", "manual", "webhook"

    # Per-platform timing in milliseconds (JSON column for flexibility)
    # Format: {"betpawa": {"duration_ms": 1234, "events_count": 40}, ...}
    platform_timings: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    errors: Mapped[list["ScrapeError"]] = relationship(
        back_populates="scrape_run",
        cascade="all, delete-orphan",
    )
    snapshots: Mapped[list["OddsSnapshot"]] = relationship(back_populates="scrape_run")

    __table_args__ = (
        Index("idx_scrape_runs_status", "status"),
        Index("idx_scrape_runs_started", "started_at"),
    )


class ScrapeError(Base):
    """Tracks individual scrape failures for debugging and monitoring."""

    __tablename__ = "scrape_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("scrape_runs.id"))
    bookmaker_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookmakers.id"), nullable=True
    )  # None if global error
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id"), nullable=True
    )  # None if bookmaker-level error
    error_type: Mapped[str] = mapped_column(
        String(50)
    )  # e.g., "timeout", "rate_limit", "parse_error", "network"
    error_message: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    scrape_run: Mapped["ScrapeRun"] = relationship(back_populates="errors")
    bookmaker: Mapped["Bookmaker | None"] = relationship()
    event: Mapped["Event | None"] = relationship()

    __table_args__ = (
        Index("idx_scrape_errors_run", "scrape_run_id"),
        Index("idx_scrape_errors_bookmaker", "bookmaker_id"),
    )
