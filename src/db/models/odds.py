"""Odds snapshot and market odds models.

This module defines the OddsSnapshot and MarketOdds models for storing
point-in-time odds data captured from bookmakers. OddsSnapshot represents
a complete odds capture for an event, while MarketOdds stores individual
market data with normalized structure.

The odds_snapshots table is partitioned by captured_at for efficient
time-range queries and data retention management.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.bookmaker import Bookmaker
    from src.db.models.event import Event
    from src.db.models.scrape import ScrapeRun


class OddsSnapshot(Base):
    """Point-in-time odds capture for an event from a bookmaker.

    Records a complete odds state for an event at a specific moment.
    This table is partitioned by captured_at in the database migration
    for efficient time-range queries and cleanup operations.

    Attributes:
        id: Primary key (BigInteger for high volume).
        event_id: FK to events table.
        bookmaker_id: FK to bookmakers table.
        captured_at: Timestamp when odds were captured.
        scrape_run_id: FK to scrape_runs (nullable).
        raw_response: Raw JSON response from bookmaker API.
        last_confirmed_at: When odds were last verified unchanged.

    Relationships:
        event: Parent Event (many-to-one).
        bookmaker: Source Bookmaker (many-to-one).
        scrape_run: Associated ScrapeRun if from scheduled scrape.
        markets: MarketOdds children (one-to-many, cascade delete).

    Note:
        Partitioning by captured_at is configured via Alembic migration,
        not in the SQLAlchemy model definition.
    """

    __tablename__ = "odds_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    bookmaker_id: Mapped[int] = mapped_column(ForeignKey("bookmakers.id"))
    captured_at: Mapped[datetime] = mapped_column(server_default=func.now())
    scrape_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("scrape_runs.id"), nullable=True
    )
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    event: Mapped["Event"] = relationship()
    bookmaker: Mapped["Bookmaker"] = relationship()
    scrape_run: Mapped["ScrapeRun | None"] = relationship(back_populates="snapshots")
    markets: Mapped[list["MarketOdds"]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_snapshots_event", "event_id"),
        Index("idx_snapshots_bookmaker", "bookmaker_id"),
        Index(
            "idx_snapshots_event_time",
            "event_id",
            "captured_at",
            postgresql_ops={"captured_at": "DESC"},
        ),
        # Note: BRIN index on captured_at added in raw SQL migration, not here
    )


class MarketOdds(Base):
    """Individual market odds within an odds snapshot.

    Stores normalized market data mapped to Betpawa market taxonomy.
    The outcomes JSON contains selection names and odds values in a
    consistent structure across all platforms.

    Attributes:
        id: Primary key (BigInteger for high volume).
        snapshot_id: FK to odds_snapshots table.
        betpawa_market_id: Normalized market ID in Betpawa taxonomy.
        betpawa_market_name: Human-readable market name.
        line: Over/under line for total markets (e.g., 2.5).
        handicap_type: Type of handicap ("asian", "european").
        handicap_home: Home team handicap value.
        handicap_away: Away team handicap value.
        outcomes: JSON array of selections with odds.
            Format: [{"name": "1", "odds": 1.85, "is_active": true}, ...]
        market_groups: Categories this market belongs to (e.g., ["main"]).

    Relationships:
        snapshot: Parent OddsSnapshot (many-to-one).
    """

    __tablename__ = "market_odds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("odds_snapshots.id")
    )
    betpawa_market_id: Mapped[str] = mapped_column(String(50))
    betpawa_market_name: Mapped[str] = mapped_column(String(255))
    line: Mapped[float | None] = mapped_column(nullable=True)
    handicap_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    handicap_home: Mapped[float | None] = mapped_column(nullable=True)
    handicap_away: Mapped[float | None] = mapped_column(nullable=True)
    outcomes: Mapped[dict] = mapped_column(JSON)
    market_groups: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    snapshot: Mapped["OddsSnapshot"] = relationship(back_populates="markets")

    __table_args__ = (
        Index("idx_market_odds_snapshot", "snapshot_id"),
        Index("idx_market_odds_market", "betpawa_market_id"),
    )
