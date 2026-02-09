"""Mapped Market Types.

Types for the mapped output - competitor data expressed in Betpawa's terms.
These represent competitor data transformed to use Betpawa's IDs and naming conventions.

Purpose: Betpawa is the reference platform. By mapping competitor data to Betpawa's
format, Betpawa can:
    - Identify markets using their native IDs
    - Act on comparison results using familiar naming
    - Easily spot discrepancies in their own terms

Model Hierarchy:
    MappedMarket: Complete mapped market with Betpawa identifiers.
        - outcomes: tuple[MappedOutcome, ...] - Individual selections.
        - handicap: MappedHandicap | None - For handicap markets.
        - line: float | None - For Over/Under markets.

All models are frozen (immutable) for thread safety and hashability.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class MappedOutcome(BaseModel):
    """Mapped Outcome - Competitor outcome in Betpawa's format.

    Represents a competitor outcome transformed to use Betpawa's naming.
    """

    model_config = ConfigDict(frozen=True)

    betpawa_outcome_name: str
    """Betpawa outcome name (e.g., '1', 'X', '2')."""

    sportybet_outcome_desc: str | None
    """Original Sportybet outcome desc for traceability, None for Bet9ja sources."""

    odds: float
    """Decimal odds (parsed from source string if needed)."""

    is_active: bool = True
    """Whether active on the source platform."""


class MappedHandicap(BaseModel):
    """Handicap data for mapped handicap markets."""

    model_config = ConfigDict(frozen=True)

    type: Literal["european", "asian"]
    """Handicap type: 'european' for 3-way (X:Y), 'asian' for 2-way."""

    home: float
    """Home team handicap value."""

    away: float
    """Away team handicap value."""


class MappedMarket(BaseModel):
    """Mapped Market - Competitor data in Betpawa's format.

    This represents a competitor market transformed to use
    Betpawa's IDs and naming conventions.
    """

    model_config = ConfigDict(frozen=True)

    betpawa_market_id: str
    """Betpawa market type ID (e.g., '3743' for 1X2)."""

    betpawa_market_name: str
    """Betpawa market name (e.g., '1X2 - FT')."""

    sportybet_market_id: str | None
    """Original Sportybet market ID for traceability, None for Bet9ja sources."""

    line: float | None = None
    """Line value for Over/Under markets (e.g., 2.5 for Over/Under 2.5)."""

    handicap: MappedHandicap | None = None
    """Handicap data for handicap markets (European 3-way or Asian 2-way)."""

    outcomes: tuple[MappedOutcome, ...]
    """Mapped outcomes (tuple for immutability)."""
