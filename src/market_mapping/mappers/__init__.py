"""Market Mappers Module.

Transforms competitor market data into Betpawa's format.
"""

from market_mapping.mappers.sportybet import map_sportybet_to_betpawa

__all__ = [
    "map_sportybet_to_betpawa",
]
