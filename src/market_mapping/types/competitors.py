"""Competitor Types.

Type definitions for the unified multi-competitor API.
Provides a discriminated union for type-safe handling of different
competitor data sources in a single function.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from market_mapping.types.sportybet import SportybetMarket


class SportybetInput(BaseModel):
    """Sportybet input wrapper for discriminated union.

    Wraps a SportybetMarket with a source discriminator.
    """

    source: Literal["sportybet"] = "sportybet"
    """Source discriminator - always 'sportybet'."""

    market: SportybetMarket
    """The Sportybet market data."""


class Bet9jaInput(BaseModel):
    """Bet9ja input wrapper for discriminated union.

    Accepts the full Bet9ja odds dict for batch processing.
    All markets in the dict will be grouped and mapped.

    Example:
        >>> odds = {"S_1X2_1": "1.50", "S_1X2_X": "3.20", "S_1X2_2": "2.10"}
        >>> input = Bet9jaInput(odds=odds)
    """

    source: Literal["bet9ja"] = "bet9ja"
    """Source discriminator - always 'bet9ja'."""

    odds: dict[str, str]
    """Full Bet9ja odds dict (key -> odds_string)."""


# Discriminated union for competitor input
# Pydantic auto-selects the correct model based on 'source' field
CompetitorInput = Annotated[
    Union[SportybetInput, Bet9jaInput],
    Field(discriminator="source"),
]
"""Discriminated union for competitor input.

Use this type with mappers for type-safe handling of different
competitor sources. Pydantic will narrow the type based on
the 'source' discriminator.

Examples:
    >>> # Sportybet input
    >>> sportybet_input = SportybetInput(market=sportybet_market)

    >>> # Bet9ja input (batch odds dict)
    >>> odds = {"S_1X2_1": "1.50", "S_1X2_X": "3.20", "S_1X2_2": "2.10"}
    >>> bet9ja_input = Bet9jaInput(odds=odds)
"""
