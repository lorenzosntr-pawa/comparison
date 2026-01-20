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

    Represents a single odds entry from Bet9ja's flattened key-value structure.

    Example:
        >>> input = Bet9jaInput(key="S_1X2_1", odds="2.15")
    """

    source: Literal["bet9ja"] = "bet9ja"
    """Source discriminator - always 'bet9ja'."""

    key: str
    """Bet9ja odds key (e.g., 'S_1X2_1', 'S_OU@2.5_O')."""

    odds: str | float
    """Odds value as string or number."""


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

    >>> # Bet9ja input
    >>> bet9ja_input = Bet9jaInput(key='S_1X2_1', odds='2.15')

    >>> # Generic input (Pydantic auto-discriminates)
    >>> data = {"source": "bet9ja", "key": "S_1X2_1", "odds": "2.15"}
"""
