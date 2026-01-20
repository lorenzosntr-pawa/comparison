"""Market Mapping Library.

Transforms competitor markets (Sportybet, Bet9ja) into Betpawa's format
for odds comparison. Maps 102 Betpawa markets with support for:
- Simple markets (1X2, Double Chance, BTTS)
- Parameterized markets (Over/Under with lines, Handicaps)
- Corner and booking markets
- Combo markets (1X2 & BTTS, Double Chance & O/U)

Example:
    >>> from market_mapping import map_to_betpawa, SportybetInput, Bet9jaInput
    >>> # Unified API - works with any competitor
    >>> result = map_to_betpawa(SportybetInput(market=sportybet_market))
    >>> # Bet9ja batch processing
    >>> results = map_to_betpawa(Bet9jaInput(odds={"S_1X2_1": "1.50", ...}))
"""

# Types
from market_mapping.types.competitors import (
    Bet9jaInput,
    CompetitorInput,
    SportybetInput,
)
from market_mapping.types.errors import MappingError, MappingErrorCode
from market_mapping.types.mapped import MappedHandicap, MappedMarket, MappedOutcome

# Mappers
from market_mapping.mappers import (
    map_bet9ja_market_to_betpawa,
    map_bet9ja_odds_to_betpawa,
    map_sportybet_to_betpawa,
    map_to_betpawa,
)

# Registry
from market_mapping.mappings import (
    MARKET_MAPPINGS,
    find_by_bet9ja_key,
    find_by_betpawa_id,
    find_by_canonical_id,
    find_by_sportybet_id,
)

__all__ = [
    # Types
    "MappingError",
    "MappingErrorCode",
    "MappedMarket",
    "MappedOutcome",
    "MappedHandicap",
    "CompetitorInput",
    "SportybetInput",
    "Bet9jaInput",
    # Mappers
    "map_to_betpawa",
    "map_sportybet_to_betpawa",
    "map_bet9ja_market_to_betpawa",
    "map_bet9ja_odds_to_betpawa",
    # Registry
    "MARKET_MAPPINGS",
    "find_by_betpawa_id",
    "find_by_sportybet_id",
    "find_by_canonical_id",
    "find_by_bet9ja_key",
]
