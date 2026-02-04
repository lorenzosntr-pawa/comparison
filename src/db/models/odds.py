"""Odds snapshot and market odds models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.bookmaker import Bookmaker
    from src.db.models.event import Event
    from src.db.models.scrape import ScrapeRun


class OddsSnapshot(Base):
    """Point-in-time odds capture for an event from a bookmaker.

    This table will be partitioned by captured_at in the migration.
    SQLAlchemy model defines structure, Alembic migration handles partitioning.
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
    """Individual market odds within a snapshot.

    Stores normalized market data with JSONB outcomes.
    Outcomes structure varies by market type, e.g.:
    [{"name": "1", "odds": 1.85, "is_active": true}, ...]
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
