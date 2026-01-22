"""Sportybet API Type Definitions.

These models match the actual JSON structure from Sportybet's event API.
Used for parsing and validating Sportybet API responses.
"""

from pydantic import BaseModel, ConfigDict, Field


def _to_camel(string: str) -> str:
    """Convert snake_case to camelCase for API compatibility."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class SportybetOutcome(BaseModel):
    """Individual outcome within a Sportybet market."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    id: str
    """Outcome identifier (e.g., '1', '2', '3')."""

    odds: str
    """Decimal odds as a string (requires parsing to number)."""

    probability: str
    """Implied probability as decimal string."""

    void_probability: str = ""
    """Void probability (usually '0E-10')."""

    is_active: int
    """Whether outcome is active: 1 = active, 0 = suspended."""

    desc: str
    """Outcome description (e.g., 'Home', 'Draw', 'Away')."""

    cash_out_is_active: int | None = None
    """Cash out availability flag (optional)."""


class SportybetMarketExtend(BaseModel):
    """Market extension mapping for related markets (1UP, 2UP)."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    name: str
    """Extension name (e.g., '1UP', '2UP')."""

    root_market_id: str
    """Root market ID this extends."""

    node_market_id: str
    """The extended market ID."""

    not_support: bool
    """Whether this extension is not supported."""


class SportybetMarket(BaseModel):
    """A market offered for a Sportybet event."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    id: str
    """Market type identifier (e.g., '1' for 1X2, '18' for Over/Under)."""

    product: int
    """Product type (3 = prematch)."""

    desc: str
    """Market description."""

    status: int
    """Market status (0 = active)."""

    group: str | None = None
    """Market group category (e.g., 'Main', 'Goals', 'Half'). Optional - some markets lack this."""

    group_id: str | None = None
    """Market group identifier. Optional - some markets lack this."""

    market_guide: str = ""
    """Help text explaining the market."""

    title: str | None = None
    """Title template (e.g., '1,X,2'). Optional - some markets lack this."""

    name: str | None = None
    """Market name (e.g., '1X2', 'Over/Under'). Optional - some markets lack this."""

    favourite: int
    """Featured market flag."""

    outcomes: list[SportybetOutcome]
    """Available outcomes for this market."""

    far_near_odds: int
    """Odds direction indicator."""

    market_extend_vos: list[SportybetMarketExtend] | None = Field(
        default=None, alias="marketExtendVOS"
    )
    """Related market extensions (1UP, 2UP mappings)."""

    early_payout_markets: list | None = None
    """Early payout market mappings."""

    source_type: str
    """Data source type (e.g., 'BET_RADAR')."""

    last_odds_change_time: int | None = None
    """Last odds change timestamp in milliseconds. Optional - some markets lack this."""

    banned: bool
    """Whether market is banned/restricted."""

    specifier: str | None = None
    """Specifier string for parameterized markets (e.g., 'total=2.5')."""


class SportybetTournament(BaseModel):
    """Tournament information."""

    id: str
    """Tournament identifier (e.g., 'sr:tournament:17')."""

    name: str
    """Tournament name (e.g., 'Premier League')."""


class SportybetCategory(BaseModel):
    """Category (country/region) information."""

    id: str
    """Category identifier (e.g., 'sr:category:1')."""

    name: str
    """Category name (e.g., 'England')."""

    tournament: SportybetTournament
    """Tournament within this category."""


class SportybetSport(BaseModel):
    """Sport information with nested hierarchy."""

    id: str
    """Sport identifier (e.g., 'sr:sport:1')."""

    name: str
    """Sport name (e.g., 'Football')."""

    category: SportybetCategory
    """Category/country within this sport."""


class SportybetEventData(BaseModel):
    """Event data within the Sportybet response."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    event_id: str
    """Event identifier (e.g., 'sr:match:61300947')."""

    game_id: str
    """Internal game identifier."""

    product_status: str
    """Product status."""

    estimate_start_time: int
    """Estimated start time in Unix milliseconds."""

    status: int
    """Event status code."""

    match_status: str
    """Match status text (e.g., 'Not start')."""

    home_team_id: str
    """Home team identifier (e.g., 'sr:competitor:35')."""

    home_team_name: str
    """Home team name."""

    away_team_name: str
    """Away team name."""

    away_team_id: str
    """Away team identifier (e.g., 'sr:competitor:17')."""

    sport: SportybetSport
    """Sport hierarchy information."""

    markets: list[SportybetMarket]
    """Available markets for this event."""


class SportybetEvent(BaseModel):
    """Complete Sportybet API response wrapper."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    biz_code: int
    """Business code (10000 = success)."""

    message: str
    """Response message."""

    data: SportybetEventData
    """Event data payload."""
