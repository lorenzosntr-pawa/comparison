"""Market Mapping Type Definitions.

This module exports all type definitions for market mapping:
- Error types (MappingErrorCode, MappingError)
- Normalized types (SourcePlatform, NormalizedSpecifier, NormalizedMarket, etc.)
- Mapped output types (MappedOutcome, MappedHandicap, MappedMarket)
- Platform-specific input types (SportybetInput, Bet9jaInput, CompetitorInput)
"""

from market_mapping.types.bet9ja import Bet9jaMarketMeta, Bet9jaOdds
from market_mapping.types.betpawa import (
    BetpawaEvent,
    BetpawaMarket,
    BetpawaMarketAdditionalInfo,
    BetpawaMarketType,
    BetpawaParticipant,
    BetpawaPrice,
    BetpawaPriceAdditionalInfo,
    BetpawaRow,
    BetpawaWidget,
)
from market_mapping.types.competitors import Bet9jaInput, CompetitorInput, SportybetInput
from market_mapping.types.errors import MappingError, MappingErrorCode
from market_mapping.types.mapped import MappedHandicap, MappedMarket, MappedOutcome
from market_mapping.types.normalized import (
    MarketMapping,
    NormalizedMarket,
    NormalizedOutcome,
    NormalizedSpecifier,
    OutcomeMapping,
    SourcePlatform,
    SpecifierType,
)
from market_mapping.types.sportybet import (
    SportybetCategory,
    SportybetEvent,
    SportybetEventData,
    SportybetMarket,
    SportybetMarketExtend,
    SportybetOutcome,
    SportybetSport,
    SportybetTournament,
)

__all__ = [
    # Error types
    "MappingErrorCode",
    "MappingError",
    # Normalized types
    "SourcePlatform",
    "SpecifierType",
    "NormalizedSpecifier",
    "NormalizedOutcome",
    "NormalizedMarket",
    "OutcomeMapping",
    "MarketMapping",
    # Mapped types
    "MappedOutcome",
    "MappedHandicap",
    "MappedMarket",
    # Sportybet types
    "SportybetOutcome",
    "SportybetMarketExtend",
    "SportybetMarket",
    "SportybetTournament",
    "SportybetCategory",
    "SportybetSport",
    "SportybetEventData",
    "SportybetEvent",
    # Betpawa types
    "BetpawaPriceAdditionalInfo",
    "BetpawaPrice",
    "BetpawaRow",
    "BetpawaMarketType",
    "BetpawaMarketAdditionalInfo",
    "BetpawaMarket",
    "BetpawaParticipant",
    "BetpawaWidget",
    "BetpawaEvent",
    # Bet9ja types
    "Bet9jaOdds",
    "Bet9jaMarketMeta",
    # Competitor union types
    "SportybetInput",
    "Bet9jaInput",
    "CompetitorInput",
]
