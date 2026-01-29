"""EventScrapeStatus model for per-event scrape status tracking.

This model tracks the scrape status for each event within a scrape run,
providing per-event observability of the new event-centric architecture.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class EventScrapeStatus(Base):
    """Per-event scrape status within a scrape run.

    Tracks which platforms were requested/scraped/failed for each event,
    enabling detailed observability and debugging of scrape issues.

    Attributes:
        id: Primary key.
        scrape_run_id: FK to scrape_runs.id.
        sportradar_id: SR ID of the event.
        status: Overall status - "completed" or "failed".
        platforms_requested: JSON list of platforms that were attempted.
        platforms_scraped: JSON list of platforms that succeeded.
        platforms_failed: JSON list of platforms that failed.
        timing_ms: Scrape duration for this event in milliseconds.
        error_details: JSON dict of platform -> error message (nullable).
        created_at: Timestamp when this record was created.
    """

    __tablename__ = "event_scrape_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("scrape_runs.id"))
    sportradar_id: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))
    platforms_requested: Mapped[list] = mapped_column(JSON)
    platforms_scraped: Mapped[list] = mapped_column(JSON)
    platforms_failed: Mapped[list] = mapped_column(JSON)
    timing_ms: Mapped[int] = mapped_column()
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        Index("idx_event_scrape_status_run", "scrape_run_id"),
        Index("idx_event_scrape_status_sr_id", "sportradar_id"),
    )
