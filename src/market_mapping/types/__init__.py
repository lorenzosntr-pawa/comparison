"""Market Mapping Type Definitions.

This module exports all type definitions for market mapping:
- Error types (MappingErrorCode, MappingError)
- Normalized types (SourcePlatform, NormalizedSpecifier, NormalizedMarket, etc.)
- Mapped output types (MappedOutcome, MappedHandicap, MappedMarket)
- Platform-specific input types (SportybetInput, Bet9jaInput, CompetitorInput)
"""

from market_mapping.types.errors import MappingError, MappingErrorCode

__all__ = [
    # Error types
    "MappingErrorCode",
    "MappingError",
]
