"""Competitor models for SportyBet and Bet9ja data storage."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.sport import Sport


class CompetitorSource(StrEnum):
    """Source platforms for competitor data."""

    SPORTYBET = "sportybet"
    BET9JA = "bet9ja"


class CompetitorTournament(Base):
    """Tournament from a competitor platform (SportyBet, Bet9ja)."""

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
    """Event from a competitor platform with SportRadar ID linkage."""

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
    """Point-in-time odds capture for a competitor event."""

    __tablename__ = "competitor_odds_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competitor_event_id: Mapped[int] = mapped_column(ForeignKey("competitor_events.id"))
    captured_at: Mapped[datetime] = mapped_column(server_default=func.now())
    scrape_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("scrape_runs.id"), nullable=True
    )
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)

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
    """Individual market odds within a competitor odds snapshot."""

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
