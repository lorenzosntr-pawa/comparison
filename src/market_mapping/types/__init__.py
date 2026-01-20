"""Market Mapping Type Definitions.

This module exports all type definitions for market mapping:
- Error types (MappingErrorCode, MappingError)
- Normalized types (SourcePlatform, NormalizedSpecifier, NormalizedMarket, etc.)
- Mapped output types (MappedOutcome, MappedHandicap, MappedMarket)
- Platform-specific input types (SportybetInput, Bet9jaInput, CompetitorInput)
"""

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
]
