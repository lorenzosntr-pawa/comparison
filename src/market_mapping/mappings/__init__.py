"""Market Mappings Module.

Static lookup tables for market ID mappings between platforms.
"""

from .market_ids import (
    HANDICAP_MARKET_IDS,
    MARKET_MAPPINGS,
    OVER_UNDER_MARKET_IDS,
    VARIANT_MARKET_IDS,
    find_by_bet9ja_key,
    find_by_betpawa_id,
    find_by_canonical_id,
    find_by_sportybet_id,
    is_handicap_market,
    is_over_under_market,
    is_variant_market,
)

__all__ = [
    # Market mappings
    "MARKET_MAPPINGS",
    # Lookup functions
    "find_by_betpawa_id",
    "find_by_sportybet_id",
    "find_by_canonical_id",
    "find_by_bet9ja_key",
    # Classification sets
    "OVER_UNDER_MARKET_IDS",
    "HANDICAP_MARKET_IDS",
    "VARIANT_MARKET_IDS",
    # Classification helpers
    "is_over_under_market",
    "is_handicap_market",
    "is_variant_market",
]
