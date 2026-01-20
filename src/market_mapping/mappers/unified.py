"""Unified Multi-Competitor Mapper.

Provides a single entry point for mapping any competitor's market data
to Betpawa format. Uses Pydantic's discriminated union for type-safe
handling of different data sources.
"""

from market_mapping.mappers.bet9ja import map_bet9ja_odds_to_betpawa
from market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from market_mapping.types.competitors import Bet9jaInput, CompetitorInput, SportybetInput
from market_mapping.types.mapped import MappedMarket


def map_to_betpawa(input_data: SportybetInput | Bet9jaInput) -> MappedMarket | list[MappedMarket]:
    """Map competitor market data to Betpawa format.

    Uses the source field to route to the correct mapper.

    Args:
        input_data: Either SportybetInput or Bet9jaInput

    Returns:
        For Sportybet: Single MappedMarket
        For Bet9ja: List of MappedMarket (from batch processing)

    Raises:
        MappingError: If the market cannot be mapped (Sportybet)
        ValueError: If source is unknown

    Example:
        >>> from market_mapping import map_to_betpawa, SportybetInput, Bet9jaInput
        >>> # Sportybet - returns single MappedMarket
        >>> result = map_to_betpawa(SportybetInput(market=sportybet_market))
        >>> print(result.betpawa_market_name)
        '1X2 - FT'
        >>> # Bet9ja - returns list of MappedMarket
        >>> odds = {"S_1X2_1": "1.50", "S_1X2_X": "3.20", "S_1X2_2": "2.10"}
        >>> results = map_to_betpawa(Bet9jaInput(odds=odds))
        >>> len(results)
        1
    """
    if input_data.source == "sportybet":
        # Sportybet: single market -> single MappedMarket
        return map_sportybet_to_betpawa(input_data.market)
    elif input_data.source == "bet9ja":
        # Bet9ja: odds dict -> list of MappedMarket
        return map_bet9ja_odds_to_betpawa(input_data.odds)
    else:
        # Should never happen due to Pydantic validation
        raise ValueError(f"Unknown source: {input_data.source}")
