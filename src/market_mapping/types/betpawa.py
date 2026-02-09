"""Betpawa API Type Definitions.

These models match the actual JSON structure from Betpawa's event API.
Used for parsing and validating Betpawa API responses.

Model Hierarchy:
    BetpawaEvent
      - participants: list[BetpawaParticipant]
      - widgets: list[BetpawaWidget]
      - markets: list[BetpawaMarket]
          - market_type: BetpawaMarketType
          - row: list[BetpawaRow]
              - prices: list[BetpawaPrice]
                  - additional_info: BetpawaPriceAdditionalInfo
          - additional_info: BetpawaMarketAdditionalInfo

Note:
    All models use camelCase aliases for JSON compatibility with the API.
    The _to_camel function handles the snake_case to camelCase conversion.
"""

from pydantic import BaseModel, ConfigDict


def _to_camel(string: str) -> str:
    """Convert snake_case to camelCase for API compatibility."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class BetpawaPriceAdditionalInfo(BaseModel):
    """Additional information attached to prices/outcomes."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    hot: bool
    """Whether this selection is highlighted as 'hot'."""

    two_up: bool
    """2-Up promotion eligibility."""

    any_up: str
    """Promotion type: 'TWO_UP', 'ONE_UP', or 'NO_UP'."""


class BetpawaPrice(BaseModel):
    """Individual price/outcome within a market row."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    id: str
    """Unique identifier for this price."""

    name: str
    """Outcome name (e.g., '1', 'X', '2', 'Over', 'Under')."""

    type_id: str
    """Outcome type identifier."""

    price: float
    """Decimal odds as a number."""

    suspended: bool
    """Whether this outcome is currently suspended."""

    handicap: str | None
    """Handicap/line value for parameterized markets (e.g., '2.5', '1:0')."""

    display_name: str
    """User-facing display name."""

    additional_info: BetpawaPriceAdditionalInfo
    """Additional metadata."""

    probability: str
    """Base64-encoded probability data."""


class BetpawaRow(BaseModel):
    """A row within a market containing grouped prices."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    id: str
    """Unique identifier for this row."""

    handicap: float | None
    """Internal handicap grouping value (not the actual line)."""

    formatted_handicap: str | None
    """Formatted handicap string for display."""

    prices: list[BetpawaPrice]
    """Array of prices/outcomes in this row."""


class BetpawaMarketType(BaseModel):
    """Market type metadata."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    id: str
    """Unique market type identifier (e.g., '3743' for 1X2)."""

    name: str
    """Internal market name (e.g., '1X2 - FT')."""

    display_name: str
    """User-facing display name (e.g., '1X2 | Full Time')."""

    explainer: str
    """Help text explaining the market."""

    priority: int
    """Display priority (lower = higher priority)."""

    tabs: list[str]
    """Tab categories this market appears in (e.g., ['popular', 'all'])."""

    handicap_type: str
    """Handicap type: '', 'NORMAL', 'EUROPEAN', or 'ASIAN'."""

    price_column_count: int
    """Number of columns for price display."""

    price_sorting_method: str
    """Method for sorting prices."""


class BetpawaMarketAdditionalInfo(BaseModel):
    """Additional information attached to markets."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    boosted: bool
    """Whether odds are boosted."""

    cashoutable: bool
    """Whether cash out is available."""

    two_up: bool
    """2-Up promotion eligibility."""


class BetpawaMarket(BaseModel):
    """A market offered for a Betpawa event."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    market_type: BetpawaMarketType
    """Market type definition."""

    row: list[BetpawaRow]
    """Array of rows containing prices (multiple rows for parameterized markets)."""

    display_name_rows: list[str]
    """Display name rows for complex markets."""

    display_name_columns: list[str]
    """Display name columns for complex markets."""

    additional_info: BetpawaMarketAdditionalInfo
    """Additional market metadata."""


class BetpawaParticipant(BaseModel):
    """Event participant (team)."""

    id: str
    """Unique team identifier."""

    name: str
    """Team name."""

    position: int
    """Position: 1 = home, 2 = away."""


class BetpawaWidget(BaseModel):
    """Widget information (data providers)."""

    id: str
    """Widget identifier."""

    type: str
    """Provider type (e.g., 'SPORTRADAR', 'GENIUSSPORTS')."""

    retention: str | None
    """Retention period (e.g., 'PREMATCH', 'INPLAY')."""


class BetpawaEvent(BaseModel):
    """Complete Betpawa event response."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    id: str
    """Unique event identifier."""

    name: str
    """Event name (e.g., 'Manchester United - Manchester City')."""

    results: dict | None = None
    """Match results (None for prematch)."""

    widgets: list[BetpawaWidget]
    """Data provider widgets."""

    participants: list[BetpawaParticipant]
    """Participating teams."""

    start_time: str
    """Event start time in ISO 8601 format."""

    markets: list[BetpawaMarket]
    """Available markets for this event."""
