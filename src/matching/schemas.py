"""Pydantic schemas for event matching API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProcessingResult(BaseModel):
    """Result from processing a batch of scraped events."""

    new_events: int
    updated_events: int
    new_tournaments: int


class OutcomeOdds(BaseModel):
    """A single outcome with its odds value."""

    name: str
    odds: float


class InlineOdds(BaseModel):
    """Inline odds for a single market (used in list view)."""

    market_id: str
    market_name: str
    line: float | None = None
    outcomes: list[OutcomeOdds]
    margin: float | None = None


class BookmakerOdds(BaseModel):
    """Odds availability info for a single bookmaker."""

    model_config = ConfigDict(from_attributes=True)

    bookmaker_slug: str
    bookmaker_name: str
    external_event_id: str
    event_url: str | None
    has_odds: bool = False
    inline_odds: list[InlineOdds] = []


class MatchedEvent(BaseModel):
    """An event matched across multiple bookmakers."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sportradar_id: str
    name: str
    home_team: str
    away_team: str
    kickoff: datetime
    tournament_id: int
    tournament_name: str
    tournament_country: str | None = None
    sport_name: str
    bookmakers: list[BookmakerOdds]
    created_at: datetime


class MatchedEventList(BaseModel):
    """Paginated list of matched events."""

    events: list[MatchedEvent]
    total: int
    page: int = 1
    page_size: int = 50


class TournamentSummary(BaseModel):
    """Summary of a tournament for filter dropdowns."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str | None


class UnmatchedEvent(BaseModel):
    """An event that exists on some platforms but not all."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sportradar_id: str
    name: str
    kickoff: datetime
    platform: str  # Which platform has it
    missing_on: list[str]  # Platforms that don't have it


# Event detail schemas for full market comparison


class OutcomeDetail(BaseModel):
    """Detailed outcome with active status."""

    name: str
    odds: float
    is_active: bool = True


class MarketOddsDetail(BaseModel):
    """Full market odds for event detail view."""

    betpawa_market_id: str
    betpawa_market_name: str
    line: float | None = None
    outcomes: list[OutcomeDetail]
    margin: float | None = None  # Calculated: (sum(1/odds) - 1) * 100
    market_groups: list[str] | None = None  # Betpawa market tabs (popular, goals, etc.)


class BookmakerMarketData(BaseModel):
    """Complete market data from a single bookmaker."""

    bookmaker_slug: str
    bookmaker_name: str
    snapshot_time: datetime | None = None
    markets: list[MarketOddsDetail]


class EventDetailResponse(MatchedEvent):
    """Extended event response with full market data per bookmaker.

    Extends MatchedEvent to maintain backward compatibility while adding
    comprehensive market comparison data.
    """

    markets_by_bookmaker: list[BookmakerMarketData] = []
