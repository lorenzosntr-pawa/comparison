"""Bet9ja Type Definitions.

Types for Bet9ja's flattened key-value market structure.
Bet9ja encodes market/outcome information in key strings:
    S_{MARKET}[@{PARAM}]_{OUTCOME}

Key Format Examples:
    - Simple: "S_1X2_1" -> market=1X2, outcome=1
    - With param: "S_OU@2.5_O" -> market=OU, param=2.5, outcome=O
    - Handicap: "S_AH@-0.5_1" -> market=AH, param=-0.5, outcome=1

Models:
    Bet9jaOdds: Single key-value pair from flattened structure.
    Bet9jaMarketMeta: Market metadata from D.MK array in API response.
"""

from pydantic import BaseModel, ConfigDict, Field


class Bet9jaOdds(BaseModel):
    """Bet9ja odds entry - a single key-value pair from the flattened structure.

    Examples:
        - {"key": "S_1X2_1", "odds": "3.5"}
        - {"key": "S_OU@2.5_O", "odds": "2.33"}
    """

    key: str
    """Bet9ja odds key (e.g., 'S_1X2_1', 'S_OU@2.5_O')."""

    odds: str | float
    """Odds value as string or number."""


class Bet9jaMarketMeta(BaseModel):
    """Bet9ja market metadata from D.MK array.

    Minimal fields needed for market identification and display.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="ID")
    """Market key prefix (e.g., 'S_OUA', 'S_1X2'), aliased from ID."""

    ds: str = Field(alias="DS")
    """Display name (e.g., 'Over/Under Asian', '1X2'), aliased from DS."""

    gcat: str | None = Field(default=None, alias="GCAT")
    """Group category (e.g., 'POPULAR', 'COMBINED', 'GOAL'), aliased from GCAT."""

    market_id: str | None = Field(default=None, alias="MARKETID")
    """Internal market ID, aliased from MARKETID."""

    sgn: list[str] | None = Field(default=None, alias="SGN")
    """Outcome display names, aliased from SGN."""

    sgnk: list[str] | None = Field(default=None, alias="SGNK")
    """Outcome key suffixes, aliased from SGNK."""
