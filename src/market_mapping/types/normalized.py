"""Normalized Market Model Types.

Platform-agnostic interfaces for the normalized market representation.
These types serve as the common ground between Betpawa and competitor structures,
enabling unified comparison and transformation logic.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

# Type aliases for platform and specifier types
SourcePlatform = Literal["betpawa", "sportybet", "bet9ja"]
"""Source platform identifier."""

SpecifierType = Literal["total", "handicap", "goalnr", "score", "other"]
"""Specifier types for parameterized markets."""


class NormalizedSpecifier(BaseModel):
    """Normalized specifier for parameterized markets.

    Used to represent line values, handicaps, goal numbers, etc.
    in a platform-agnostic way.

    Examples:
        - Over/Under 2.5: NormalizedSpecifier(type="total", value=2.5, raw="total=2.5")
        - Handicap 0:1: NormalizedSpecifier(type="handicap", value="0:1", raw="hcp=0:1")
        - First Goal: NormalizedSpecifier(type="goalnr", value=1, raw="goalnr=1")
    """

    model_config = ConfigDict(frozen=True)

    type: SpecifierType
    """Type of specifier."""

    value: str | float | int
    """The line/handicap/goal number value."""

    raw: str
    """Original specifier string for debugging/traceability."""


class NormalizedOutcome(BaseModel):
    """Normalized outcome within a market.

    Represents a single selectable outcome with unified structure
    regardless of source platform.
    """

    model_config = ConfigDict(frozen=True)

    outcome_id: str
    """Internal canonical outcome ID (e.g., 'home', 'draw', 'away', 'over', 'under')."""

    name: str
    """Human-readable display name."""

    odds: float
    """Decimal odds as a number (always numeric)."""

    is_active: bool
    """Whether this outcome is currently available for betting."""

    source_outcome_id: str
    """Original outcome ID from the source platform."""


class NormalizedMarket(BaseModel):
    """Normalized market representation.

    Platform-agnostic market structure that can be created from
    either Betpawa or competitor source data.
    """

    model_config = ConfigDict(frozen=True)

    market_id: str
    """Internal canonical market ID (e.g., '1x2_ft', 'over_under_ft')."""

    name: str
    """Human-readable market name."""

    specifier: NormalizedSpecifier | None
    """Specifier for parameterized markets, None for simple markets like 1X2."""

    outcomes: tuple[NormalizedOutcome, ...]
    """Tuple of outcomes in this market (tuple for immutability)."""

    source_market_id: str
    """Original market ID from the source platform."""

    source_platform: SourcePlatform
    """Which platform this market was normalized from."""


class OutcomeMapping(BaseModel):
    """Outcome mapping definition.

    Maps canonical outcome IDs to platform-specific names/descriptions.
    Used for matching outcomes between platforms.
    """

    model_config = ConfigDict(frozen=True)

    canonical_id: str
    """Canonical outcome identifier (e.g., 'home', 'draw', 'away', 'over', 'under')."""

    betpawa_name: str | None
    """Betpawa outcome name (e.g., '1', 'X', '2'), None if not on Betpawa."""

    sportybet_desc: str | None
    """Sportybet outcome description (e.g., 'Home', 'Draw'), None if not on Sportybet."""

    bet9ja_suffix: str | None = None
    """Bet9ja outcome suffix (e.g., '1', 'X', '2', 'O', 'U'), None if not on Bet9ja."""

    position: int
    """0-indexed position for fallback matching when name/desc matching fails."""


class MarketMapping(BaseModel):
    """Market mapping definition.

    Static mapping between canonical market IDs and platform-specific IDs.
    Used to identify equivalent markets across platforms.
    """

    model_config = ConfigDict(frozen=True)

    canonical_id: str
    """Canonical market identifier (e.g., '1x2_ft', 'double_chance_ft')."""

    name: str
    """Human-readable market name."""

    betpawa_id: str | None
    """Betpawa market type ID, None if not on Betpawa."""

    sportybet_id: str | None
    """Sportybet market ID, None if not on Sportybet."""

    bet9ja_key: str | None = None
    """Bet9ja market key prefix (e.g., 'S_1X2'), None if not on Bet9ja."""

    outcome_mapping: tuple[OutcomeMapping, ...]
    """Outcome mappings for this market (tuple for immutability)."""
