"""Scrape run and error tracking models.

This module defines models for tracking scrape execution: ScrapeRun for
individual scrape operations, ScrapeBatch for grouping related runs,
ScrapeError for failure tracking, and ScrapePhaseLog for phase-level
audit trails.
"""

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
    """Status values for scrape run tracking.

    Used in ScrapeRun.status and ScrapeBatch.status columns to indicate
    the current state of a scrape operation.

    Values:
        PENDING: Scrape scheduled but not yet started.
        RUNNING: Scrape currently in progress.
        COMPLETED: All platforms scraped successfully.
        PARTIAL: Some platforms succeeded, some failed.
        FAILED: All platforms failed.
        CONNECTION_FAILED: Network/connection error prevented scrape.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some bookmakers succeeded, some failed
    FAILED = "failed"
    CONNECTION_FAILED = "connection_failed"


class ScrapeBatch(Base):
    """Groups multiple ScrapeRuns for unified batch visibility.

    A batch represents a single logical scraping operation that may spawn
    separate runs per platform. Enables aggregated UI views showing status
    across all platforms (e.g., "Batch 123: betpawa OK, sportybet OK, bet9ja FAILED").

    Attributes:
        id: Primary key.
        started_at: When the batch was initiated.
        completed_at: When all runs finished (nullable).
        status: Aggregate status of the batch.
        trigger: How batch was initiated ("scheduled", "manual").
        notes: Optional notes about the batch.

    Relationships:
        runs: Child ScrapeRun entries (one-to-many, cascade delete).
    """

    __tablename__ = "scrape_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[ScrapeStatus] = mapped_column(
        String(20), default=ScrapeStatus.PENDING
    )
    trigger: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g., "scheduled", "manual"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    runs: Mapped[list["ScrapeRun"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("idx_scrape_batches_started", "started_at"),)


class ScrapeRun(Base):
    """Tracks each scraping execution for operational monitoring.

    Records metadata about a single scrape execution including timing,
    event counts, and per-platform status. Used for monitoring dashboards
    and debugging scrape issues.

    Attributes:
        id: Primary key.
        batch_id: FK to scrape_batches (nullable for backwards compat).
        status: Current run status (ScrapeStatus value).
        started_at: When the run began.
        completed_at: When the run finished (nullable).
        events_scraped: Count of successfully scraped events.
        events_failed: Count of failed events.
        trigger: How run was initiated ("scheduled", "manual", "webhook").
        platform_timings: JSON with per-platform timing data.
            Format: {"betpawa": {"duration_ms": 1234, "events_count": 40}}
        current_phase: Active phase name for progress tracking.
        current_platform: Active platform for progress tracking.
        platform_status: JSON with per-platform status.
            Format: {"betpawa": "completed", "sportybet": "active"}

    Relationships:
        batch: Parent ScrapeBatch if part of a batch (many-to-one).
        errors: ScrapeError children (one-to-many, cascade delete).
        snapshots: OddsSnapshot entries created by this run.
        phase_logs: ScrapePhaseLog children (one-to-many, cascade delete).
    """

    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("scrape_batches.id"), nullable=True
    )  # nullable for backwards compatibility
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

    # Phase tracking fields for granular state visibility
    current_phase: Mapped[str | None] = mapped_column(String(30), nullable=True)
    current_platform: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Format: {"betpawa": "completed", "sportybet": "active", "bet9ja": "pending"}
    platform_status: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    batch: Mapped["ScrapeBatch | None"] = relationship(back_populates="runs")
    errors: Mapped[list["ScrapeError"]] = relationship(
        back_populates="scrape_run",
        cascade="all, delete-orphan",
    )
    snapshots: Mapped[list["OddsSnapshot"]] = relationship(back_populates="scrape_run")
    phase_logs: Mapped[list["ScrapePhaseLog"]] = relationship(
        back_populates="scrape_run",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_scrape_runs_status", "status"),
        Index("idx_scrape_runs_started", "started_at"),
    )


class ScrapeError(Base):
    """Tracks individual scrape failures for debugging and monitoring.

    Records error details when a scrape operation fails at the bookmaker
    or event level. Enables error analysis and alerting.

    Attributes:
        id: Primary key.
        scrape_run_id: FK to scrape_runs table.
        bookmaker_id: FK to bookmakers (null if global error).
        event_id: FK to events (null if bookmaker-level error).
        error_type: Category of error (e.g., "timeout", "rate_limit").
        error_message: Detailed error description.
        occurred_at: Timestamp when error occurred.

    Relationships:
        scrape_run: Parent ScrapeRun (many-to-one).
        bookmaker: Associated Bookmaker if platform-specific error.
        event: Associated Event if event-level error.
    """

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


class ScrapePhaseLog(Base):
    """Tracks phase transitions during a scrape run for audit trail.

    Records the start and end of each phase within a scrape execution,
    enabling detailed timeline reconstruction and performance analysis.

    Attributes:
        id: Primary key.
        scrape_run_id: FK to scrape_runs table.
        platform: Platform being processed (nullable for global phases).
        phase: Phase name (e.g., "fetch_events", "save_odds").
        started_at: When this phase began.
        ended_at: When this phase completed (nullable if still running).
        events_processed: Count of events processed in this phase.
        message: Optional status or progress message.
        error_details: JSON with error info if phase failed.

    Relationships:
        scrape_run: Parent ScrapeRun (many-to-one).
    """

    __tablename__ = "scrape_phase_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("scrape_runs.id"))
    platform: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phase: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    events_processed: Mapped[int | None] = mapped_column(nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationship back to parent scrape run
    scrape_run: Mapped["ScrapeRun"] = relationship(back_populates="phase_logs")

    __table_args__ = (Index("idx_scrape_phase_logs_run_id", "scrape_run_id"),)
