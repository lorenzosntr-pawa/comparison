"""Availability detection for market tracking.

Compares cached market data against newly scraped markets to detect
when markets become unavailable (disappeared from bookmaker) or return
(were unavailable, now available again).

Functions:
    get_market_key(): Generate unique key for market comparison
    detect_availability_changes(): Compare previous cache to new scrape
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any

import structlog

from src.caching.odds_cache import CachedMarket

logger = structlog.get_logger(__name__)


def get_market_key(market: CachedMarket | dict[str, Any]) -> tuple[str, float | None]:
    """Generate unique key for market comparison.

    Args:
        market: CachedMarket instance or dict with betpawa_market_id and line

    Returns:
        Tuple of (betpawa_market_id, line) for dictionary lookup
    """
    if isinstance(market, CachedMarket):
        return (market.betpawa_market_id, market.line)
    return (str(market.get("betpawa_market_id", "")), market.get("line"))


def detect_availability_changes(
    previous_markets: dict[tuple[str, float | None], CachedMarket],
    new_market_data: list[Any],
    timestamp: datetime,
) -> tuple[list[CachedMarket], list[CachedMarket], list[tuple[str, float | None]]]:
    """Compare previous cache state to new scrape results.

    Detects:
    - Markets that disappeared (were available, now missing)
    - Markets that returned (were unavailable, now present)

    Args:
        previous_markets: Dict of market_key -> CachedMarket from cache
        new_market_data: List of newly scraped market objects (ORM or dict)
        timestamp: Current timestamp for unavailable_at

    Returns:
        Tuple of:
        - became_unavailable: CachedMarket instances with unavailable_at set
        - became_available: CachedMarket instances with unavailable_at cleared
        - disappeared_keys: Market keys that disappeared (for logging)
    """
    # Build set of keys from new scrape
    new_keys: set[tuple[str, float | None]] = set()
    for m in new_market_data:
        if isinstance(m, dict):
            key = (str(m.get("betpawa_market_id", "")), m.get("line"))
        else:
            key = (str(m.betpawa_market_id), m.line)
        new_keys.add(key)

    previous_keys = set(previous_markets.keys())

    # Markets that were available but are now missing
    disappeared_keys = previous_keys - new_keys

    # Markets that are in new scrape
    present_keys = new_keys & previous_keys

    became_unavailable: list[CachedMarket] = []
    became_available: list[CachedMarket] = []

    # Check disappeared markets
    for key in disappeared_keys:
        prev = previous_markets[key]
        if prev.unavailable_at is None:  # Was available, now gone
            # Create updated market with unavailable_at set
            became_unavailable.append(replace(prev, unavailable_at=timestamp))

    # Check present markets that were previously unavailable
    for key in present_keys:
        prev = previous_markets[key]
        if prev.unavailable_at is not None:  # Was unavailable, now back
            # Create updated market with unavailable_at cleared
            became_available.append(replace(prev, unavailable_at=None))

    if became_unavailable or became_available:
        logger.info(
            "availability_detection.changes",
            became_unavailable=len(became_unavailable),
            became_available=len(became_available),
            disappeared_keys_count=len(disappeared_keys),
        )

    return became_unavailable, became_available, list(disappeared_keys)
