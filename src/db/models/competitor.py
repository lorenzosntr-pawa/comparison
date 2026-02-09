"""Competitor models for SportyBet and Bet9ja data storage.

This module defines models for storing raw data from competitor platforms
(SportyBet, Bet9ja) before matching to Betpawa events. The competitor_*
tables mirror the Betpawa data structure but store platform-specific IDs
and are linked via SportRadar IDs for cross-platform matching.
"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.sport import Sport


class CompetitorSource(StrEnum):
    """Source platforms for competitor data.

    Identifies which competitor platform the data originated from.
    Used in source columns to distinguish SportyBet vs Bet9ja records.
    """

    SPORTYBET = "sportybet"
    BET9JA = "bet9ja"


class CompetitorTournament(Base):
    """Tournament from a competitor platform (SportyBet, Bet9ja).

    Stores tournament metadata from competitor platforms before matching
    to Betpawa tournaments. Links to Sport for categorization.

    Attributes:
        id: Primary key.
        source: Platform identifier ("sportybet" or "bet9ja").
        sport_id: FK to sports table.
        name: Tournament display name from source platform.
        country_raw: Raw country string from source platform.
        country_iso: Normalized ISO 3166-1 alpha-3 country code.
        external_id: Platform-specific tournament ID.
        sportradar_id: Cross-platform matching key (nullable).
        created_at: Timestamp when record was created.
        deleted_at: Soft delete timestamp for logical deletion.

    Relationships:
        sport: Parent Sport entity (many-to-one).
        events: CompetitorEvent children (one-to-many, cascade delete).

    Constraints:
        - Unique on (source, external_id): One record per platform tournament.
    """

    __tablename__ = "competitor_tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(20))  # CompetitorSource value
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"))
    name: Mapped[str] = mapped_column(String(255))
    country_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_iso: Mapped[str | None] = mapped_column(String(3), nullable=True)
    external_id: Mapped[str] = mapped_column(String(100))
    sportradar_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    sport: Mapped["Sport"] = relationship()
    events: Mapped[list["CompetitorEvent"]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_competitor_tournaments_source_external"),
        Index("idx_competitor_tournaments_source", "source"),
        Index("idx_competitor_tournaments_sport", "sport_id"),
        Index(
            "idx_competitor_tournaments_sr_id",
            "sportradar_id",
            postgresql_where="sportradar_id IS NOT NULL",
        ),
    )


class CompetitorEvent(Base):
    """Event from a competitor platform with SportRadar ID linkage.

    Stores event data from SportyBet or Bet9ja. The sportradar_id field
    enables matching to Betpawa events for odds comparison.

    Attributes:
        id: Primary key.
        source: Platform identifier ("sportybet" or "bet9ja").
        tournament_id: FK to competitor_tournaments.
        betpawa_event_id: FK to events table when matched (nullable).
        name: Event display name (e.g., "Arsenal vs Chelsea").
        home_team: Home team name.
        away_team: Away team name.
        kickoff: Event start time (UTC).
        external_id: Platform-specific event ID.
        sportradar_id: Cross-platform matching key (required).
        created_at: Timestamp when record was created.
        updated_at: Timestamp of last modification.
        deleted_at: Soft delete timestamp for logical deletion.

    Relationships:
        tournament: Parent CompetitorTournament (many-to-one).
        betpawa_event: Matched Betpawa Event if linked (many-to-one).
        odds_snapshots: CompetitorOddsSnapshot children (one-to-many).

    Constraints:
        - Unique on (source, external_id): One record per platform event.
    """

    __tablename__ = "competitor_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(20))  # CompetitorSource value
    tournament_id: Mapped[int] = mapped_column(ForeignKey("competitor_tournaments.id"))
    betpawa_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(500))
    home_team: Mapped[str] = mapped_column(String(255))
    away_team: Mapped[str] = mapped_column(String(255))
    kickoff: Mapped[datetime] = mapped_column()
    external_id: Mapped[str] = mapped_column(String(100))
    sportradar_id: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    tournament: Mapped["CompetitorTournament"] = relationship(back_populates="events")
    betpawa_event: Mapped["Event | None"] = relationship()
    odds_snapshots: Mapped[list["CompetitorOddsSnapshot"]] = relationship(
        back_populates="competitor_event",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_competitor_events_source_external"),
        Index("idx_competitor_events_source", "source"),
        Index("idx_competitor_events_tournament", "tournament_id"),
        Index("idx_competitor_events_sr_id", "sportradar_id"),
        Index(
            "idx_competitor_events_betpawa",
            "betpawa_event_id",
            postgresql_where="betpawa_event_id IS NOT NULL",
        ),
        Index("idx_competitor_events_kickoff", "kickoff"),
    )


# Import for TYPE_CHECKING at module level for Event reference
if TYPE_CHECKING:
    from src.db.models.event import Event
    from src.db.models.scrape import ScrapeRun


class CompetitorOddsSnapshot(Base):
    """Point-in-time odds capture for a competitor event.

    Records a complete odds state for a competitor event at a specific
    moment in time. Contains the raw API response and links to normalized
    market data via CompetitorMarketOdds.

    Attributes:
        id: Primary key (auto-increment).
        competitor_event_id: FK to competitor_events.
        captured_at: Timestamp when odds were captured.
        scrape_run_id: FK to scrape_runs (nullable).
        raw_response: Raw JSON response from platform API.
        last_confirmed_at: When odds were last confirmed unchanged.

    Relationships:
        competitor_event: Parent CompetitorEvent (many-to-one).
        scrape_run: Associated ScrapeRun if captured during scheduled scrape.
        markets: CompetitorMarketOdds children (one-to-many, cascade delete).
    """

    __tablename__ = "competitor_odds_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competitor_event_id: Mapped[int] = mapped_column(ForeignKey("competitor_events.id"))
    captured_at: Mapped[datetime] = mapped_column(server_default=func.now())
    scrape_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("scrape_runs.id"), nullable=True
    )
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    competitor_event: Mapped["CompetitorEvent"] = relationship(
        back_populates="odds_snapshots"
    )
    scrape_run: Mapped["ScrapeRun | None"] = relationship()
    markets: Mapped[list["CompetitorMarketOdds"]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_competitor_odds_snapshots_event", "competitor_event_id"),
        Index("idx_competitor_odds_snapshots_captured", "captured_at"),
    )


class CompetitorMarketOdds(Base):
    """Individual market odds within a competitor odds snapshot.

    Stores normalized market data mapped to Betpawa market taxonomy.
    The outcomes JSON contains selection names and odds values.

    Attributes:
        id: Primary key (auto-increment).
        snapshot_id: FK to competitor_odds_snapshots.
        betpawa_market_id: Normalized market ID in Betpawa taxonomy.
        betpawa_market_name: Human-readable market name.
        line: Over/under line for total markets (e.g., 2.5).
        handicap_type: Type of handicap ("asian", "european").
        handicap_home: Home team handicap value.
        handicap_away: Away team handicap value.
        outcomes: JSON array of selections with odds.
            Format: [{"name": "1", "odds": 1.85, "is_active": true}, ...]
        market_groups: Categories this market belongs to.

    Relationships:
        snapshot: Parent CompetitorOddsSnapshot (many-to-one).
    """

    __tablename__ = "competitor_market_odds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("competitor_odds_snapshots.id"))
    betpawa_market_id: Mapped[str] = mapped_column(String(50))
    betpawa_market_name: Mapped[str] = mapped_column(String(255))
    line: Mapped[float | None] = mapped_column(nullable=True)
    handicap_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    handicap_home: Mapped[float | None] = mapped_column(nullable=True)
    handicap_away: Mapped[float | None] = mapped_column(nullable=True)
    outcomes: Mapped[dict] = mapped_column(JSON)
    market_groups: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    snapshot: Mapped["CompetitorOddsSnapshot"] = relationship(back_populates="markets")

    __table_args__ = (
        Index("idx_competitor_market_odds_snapshot", "snapshot_id"),
        Index("idx_competitor_market_odds_market", "betpawa_market_id"),
    )
