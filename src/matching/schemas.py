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
    outcomes: list[OutcomeOdds]


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
    sport_name: str
    bookmakers: list[BookmakerOdds]
    created_at: datetime


class MatchedEventList(BaseModel):
    """Paginated list of matched events."""

    events: list[MatchedEvent]
    total: int
    page: int = 1
    page_size: int = 50


class UnmatchedEvent(BaseModel):
    """An event that exists on some platforms but not all."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sportradar_id: str
    name: str
    kickoff: datetime
    platform: str  # Which platform has it
    missing_on: list[str]  # Platforms that don't have it
