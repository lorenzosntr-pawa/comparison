"""Market-level odds models for current state and history.

This module defines the MarketOddsCurrent and MarketOddsHistory models for the
new market-level storage architecture. These replace the snapshot-based approach
(OddsSnapshot + MarketOdds) with a more efficient UPSERT pattern for current
state and append-only history for odds changes.

Key features:
- MarketOddsCurrent: Single row per market (UPSERT pattern)
- MarketOddsHistory: Append-only for changed markets (partitioned)
- Unified storage for BetPawa and competitors via bookmaker_slug

Created as part of Phase 106 (Schema Migration) for 95% storage reduction.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class MarketOddsCurrent(Base):
    """Current state of market odds for an event from a bookmaker.

    Stores the latest odds for each market using UPSERT pattern. One row per
    unique (event_id, bookmaker_slug, betpawa_market_id, line) combination.

    The table has a unique index using COALESCE(line, 0) to handle NULL lines:
        idx_moc_unique ON (event_id, bookmaker_slug, betpawa_market_id, COALESCE(line, 0))

    Attributes:
        id: Primary key (BigInteger for high volume).
        event_id: BetPawa event ID (can be negative for competitor-only events).
        bookmaker_slug: Bookmaker identifier ('betpawa', 'sportybet', 'bet9ja').
        betpawa_market_id: Normalized market ID in BetPawa taxonomy.
        betpawa_market_name: Human-readable market name.
        line: Over/under line for total markets (e.g., 2.5).
        handicap_type: Type of handicap ('asian', 'european').
        handicap_home: Home team handicap value.
        handicap_away: Away team handicap value.
        outcomes: JSON array of selections with odds.
            Format: [{"name": "1", "odds": 1.85, "is_active": true}, ...]
        market_groups: Categories this market belongs to (e.g., ["main"]).
        unavailable_at: When the market became unavailable (null if available).
        last_updated_at: When odds actually changed (for detecting changes).
        last_confirmed_at: When odds were last verified (even if unchanged).

    Note:
        No FK to events table - event_id can be negative for competitor-only events.
        Relationships will be added in Phase 108 when read paths are updated.
    """

    __tablename__ = "market_odds_current"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[int] = mapped_column(nullable=False)
    bookmaker_slug: Mapped[str] = mapped_column(String(20), nullable=False)
    betpawa_market_id: Mapped[str] = mapped_column(String(50), nullable=False)
    betpawa_market_name: Mapped[str] = mapped_column(String(255), nullable=False)
    line: Mapped[float | None] = mapped_column(Float, nullable=True)
    handicap_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    handicap_home: Mapped[float | None] = mapped_column(Float, nullable=True)
    handicap_away: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcomes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    market_groups: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    unavailable_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        # Note: UNIQUE constraint with COALESCE created via raw SQL in migration
        Index("idx_moc_event", "event_id"),
        Index("idx_moc_bookmaker", "bookmaker_slug"),
        Index("idx_moc_event_bookmaker", "event_id", "bookmaker_slug"),
    )


class MarketOddsHistory(Base):
    """Historical record of market odds changes.

    Append-only table for storing odds snapshots when markets change.
    Only inserted when odds actually differ from previous capture.
    This is a partitioned table - partitions are created via migration.

    Partitioning:
        Monthly by captured_at (PARTITION BY RANGE)
        Enables efficient time-range queries and retention cleanup

    Attributes:
        id: Primary key (BigInteger for high volume).
        event_id: BetPawa event ID (can be negative for competitor-only events).
        bookmaker_slug: Bookmaker identifier ('betpawa', 'sportybet', 'bet9ja').
        betpawa_market_id: Normalized market ID in BetPawa taxonomy.
        line: Over/under line for total markets (e.g., 2.5).
        outcomes: JSON array of selections with odds at capture time.
        captured_at: Timestamp when this odds state was captured.

    Note:
        - No handicap fields (not needed for history charts)
        - No FK to events table - allows negative event_id for competitor-only
        - PRIMARY KEY includes captured_at for partitioning support
        - Partitions created in migration: 2026_02, 2026_03, 2026_04
    """

    __tablename__ = "market_odds_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[int] = mapped_column(nullable=False)
    bookmaker_slug: Mapped[str] = mapped_column(String(20), nullable=False)
    betpawa_market_id: Mapped[str] = mapped_column(String(50), nullable=False)
    line: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcomes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, nullable=False
    )

    __table_args__ = (
        Index(
            "idx_moh_event_market_time",
            "event_id",
            "betpawa_market_id",
            "captured_at",
            postgresql_ops={"captured_at": "DESC"},
        ),
        Index("idx_moh_bookmaker_market", "bookmaker_slug", "betpawa_market_id"),
    )
