"""Pydantic schemas for palimpsest comparison API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlatformCoverage(BaseModel):
    """Per-platform coverage statistics."""

    platform: str = Field(description="Platform slug: 'sportybet' or 'bet9ja'")
    total_events: int = Field(description="Total events on this platform")
    matched_events: int = Field(description="Events matched to BetPawa")
    unmatched_events: int = Field(description="Events not matched to BetPawa")
    match_rate: float = Field(description="Percentage of events matched (0-100)")


class TournamentCoverage(BaseModel):
    """Coverage statistics for a single tournament."""

    total: int = Field(description="Total unique events in tournament")
    matched: int = Field(description="Events on both BetPawa and competitors")
    betpawa_only: int = Field(description="Events only on BetPawa")
    competitor_only: int = Field(description="Events only on competitors")


class CoverageStats(BaseModel):
    """Overall coverage statistics across all platforms."""

    total_events: int = Field(
        description="Total unique events across all platforms"
    )
    matched_count: int = Field(
        description="Events present on BetPawa AND at least one competitor"
    )
    betpawa_only_count: int = Field(
        description="Events only on BetPawa"
    )
    competitor_only_count: int = Field(
        description="Events only on competitors (not on BetPawa)"
    )
    match_rate: float = Field(
        description="Percentage of total events that are matched (0-100)"
    )
    by_platform: list[PlatformCoverage] = Field(
        description="Coverage breakdown per competitor platform"
    )


class PalimpsestEvent(BaseModel):
    """Event with cross-platform availability information."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Event ID (event.id or competitor_event.id)")
    sportradar_id: str = Field(description="SportRadar unique identifier")
    name: str = Field(description="Event name (home vs away)")
    home_team: str
    away_team: str
    kickoff: datetime
    tournament_name: str
    tournament_country: str | None = None
    sport_name: str
    availability: str = Field(
        description="One of: 'betpawa-only', 'competitor-only', 'matched'"
    )
    platforms: list[str] = Field(
        description="Platforms with this event (e.g., ['betpawa', 'sportybet'])"
    )


class TournamentGroup(BaseModel):
    """Events grouped by tournament with coverage summary."""

    tournament_id: int
    tournament_name: str
    tournament_country: str | None = None
    sport_name: str
    coverage: TournamentCoverage
    events: list[PalimpsestEvent]


class PalimpsestEventsResponse(BaseModel):
    """Full palimpsest events response with coverage and grouped events."""

    coverage: CoverageStats
    tournaments: list[TournamentGroup]
