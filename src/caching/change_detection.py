"""Change detection for incremental upserts.

Compares cached market data against newly scraped markets to determine
whether a snapshot needs to be written (odds changed) or just confirmed
(odds unchanged, update last_confirmed_at on existing row).

Algorithm:
    1. Normalize outcomes by sorting on (name, odds, is_active)
    2. Build lookup by (betpawa_market_id, line) for cached markets
    3. Compare each new market against cached version
    4. Any difference = changed; all identical = unchanged

This reduces database writes by ~70-80% in typical operation since
most markets don't change between scrape cycles (5-minute interval).

Functions:
    markets_changed(): Compare single cached vs new market set
    classify_batch_changes(): Batch classification for coordinator (snapshot-level)
    classify_market_changes(): Market-level change detection for Phase 107+

Usage:
    changed_bp, changed_comp, unchanged_bp_ids, unchanged_comp_ids = \\
        classify_batch_changes(cache, betpawa_snapshots, competitor_snapshots)
    # Only insert changed snapshots; UPDATE last_confirmed_at for unchanged

    # NEW: Market-level (Phase 107+)
    market_writes = classify_market_changes(cache, markets_by_event_bookmaker)
    # Each MarketCurrentWrite has changed=True/False per market
"""

from __future__ import annotations

from typing import Any

import structlog

from src.caching.odds_cache import CachedMarket, CachedSnapshot, OddsCache

logger = structlog.get_logger(__name__)


def _normalise_outcomes(outcomes: list[dict[str, Any]]) -> list[tuple]:
    """Sort outcomes by name and return a comparable list of tuples.

    Each outcome dict has {name, odds, is_active}.  We normalise to a
    sorted list of (name, odds, is_active) tuples so ordering differences
    don't cause false positives.
    """
    return sorted(
        (o.get("name"), o.get("odds"), o.get("is_active")) for o in outcomes
    )


def markets_changed(
    cached_markets: tuple[CachedMarket, ...] | None,
    new_markets: list[Any],
) -> bool:
    """Compare cached markets against newly scraped markets.

    Parameters
    ----------
    cached_markets:
        The markets from the cached snapshot (tuple of CachedMarket), or
        None if this event+bookmaker has never been scraped / isn't cached.
    new_markets:
        List of newly scraped market objects.  Each must have attributes or
        keys ``betpawa_market_id``, ``line``, and ``outcomes``.  Works with
        both ORM model instances (MarketOdds / CompetitorMarketOdds) and
        plain dicts.

    Returns
    -------
    bool
        True if markets have changed (snapshot must be written).
        False if markets are identical (only update last_confirmed_at).
    """
    # First scrape or cache miss — must write.
    if cached_markets is None:
        return True

    # Different market count — changed.
    if len(cached_markets) != len(new_markets):
        return True

    # Build lookup for cached markets by (betpawa_market_id, line).
    cached_lookup: dict[tuple[str, float | None], CachedMarket] = {}
    for cm in cached_markets:
        key = (cm.betpawa_market_id, cm.line)
        cached_lookup[key] = cm

    # Compare each new market against cached.
    for nm in new_markets:
        # Support both ORM objects and dicts.
        if isinstance(nm, dict):
            market_id = str(nm.get("betpawa_market_id", ""))
            line = nm.get("line")
            outcomes = nm.get("outcomes", [])
        else:
            market_id = str(nm.betpawa_market_id)
            line = nm.line
            outcomes = nm.outcomes if isinstance(nm.outcomes, list) else []

        key = (market_id, line)
        cached_market = cached_lookup.get(key)

        # Market not found in cache — new market appeared.
        if cached_market is None:
            return True

        # Compare outcomes (normalised to handle ordering differences).
        cached_outcomes = _normalise_outcomes(cached_market.outcomes)
        new_outcomes = _normalise_outcomes(outcomes)

        if cached_outcomes != new_outcomes:
            return True

    # All markets matched.
    return False


def classify_batch_changes(
    cache: OddsCache,
    betpawa_snapshots: list[tuple[int, int, list[Any]]],
    competitor_snapshots: list[tuple[int, str, list[Any]]],
) -> tuple[
    list[tuple[int, int, list[Any]]],
    list[tuple[int, str, list[Any]]],
    list[int],
    list[int],
]:
    """Classify scraped snapshots into changed vs unchanged.

    Parameters
    ----------
    cache:
        The OddsCache instance holding current cached data.
    betpawa_snapshots:
        List of (event_id, bookmaker_id, markets_data) tuples from scraping.
    competitor_snapshots:
        List of (event_id, source, markets_data) tuples from scraping.

    Returns
    -------
    tuple of:
        changed_betpawa: snapshots that need INSERT (odds changed)
        changed_competitor: snapshots that need INSERT (odds changed)
        unchanged_betpawa_ids: existing snapshot IDs that need last_confirmed_at UPDATE
        unchanged_competitor_ids: existing snapshot IDs that need last_confirmed_at UPDATE
    """
    changed_betpawa: list[tuple[int, int, list[Any]]] = []
    unchanged_betpawa_ids: list[int] = []

    for event_id, bookmaker_id, markets_data in betpawa_snapshots:
        by_bookmaker = cache.get_betpawa_snapshot(event_id)
        cached_snap: CachedSnapshot | None = None
        if by_bookmaker is not None:
            cached_snap = by_bookmaker.get(bookmaker_id)

        cached_markets = cached_snap.markets if cached_snap is not None else None

        if markets_changed(cached_markets, markets_data):
            changed_betpawa.append((event_id, bookmaker_id, markets_data))
        else:
            # Odds unchanged — record existing snapshot ID for confirmation.
            assert cached_snap is not None  # markets_changed returns True for None
            unchanged_betpawa_ids.append(cached_snap.snapshot_id)

    changed_competitor: list[tuple[int, str, list[Any]]] = []
    unchanged_competitor_ids: list[int] = []

    for event_id, source, markets_data in competitor_snapshots:
        by_source = cache.get_competitor_snapshot(event_id)
        cached_snap = None
        if by_source is not None:
            cached_snap = by_source.get(source)

        cached_markets = cached_snap.markets if cached_snap is not None else None

        if markets_changed(cached_markets, markets_data):
            changed_competitor.append((event_id, source, markets_data))
        else:
            assert cached_snap is not None
            unchanged_competitor_ids.append(cached_snap.snapshot_id)

    logger.debug(
        "change_detection.classify",
        betpawa_changed=len(changed_betpawa),
        betpawa_unchanged=len(unchanged_betpawa_ids),
        competitor_changed=len(changed_competitor),
        competitor_unchanged=len(unchanged_competitor_ids),
    )

    return changed_betpawa, changed_competitor, unchanged_betpawa_ids, unchanged_competitor_ids


def classify_market_changes(
    cache: OddsCache,
    markets: list[tuple[int, str, list[Any]]],
) -> list["MarketCurrentWrite"]:
    """Compare each market against cached version and return MarketCurrentWrite list.

    Unlike classify_batch_changes which returns entire snapshots as changed/unchanged,
    this returns per-market change status via the `changed` boolean.

    For each market in input:
    - If no cached version exists: changed=True (new market)
    - If cached outcomes differ: changed=True (odds changed)
    - If cached outcomes identical: changed=False (just confirm)

    All markets get written to market_odds_current (UPSERT), but only
    changed=True markets get written to market_odds_history (INSERT).

    Parameters
    ----------
    cache:
        The OddsCache instance holding current cached data.
    markets:
        List of (event_id, bookmaker_slug, markets_data) tuples.
        - bookmaker_slug: 'betpawa', 'sportybet', or 'bet9ja'
        - markets_data: list of market dicts or objects with betpawa_market_id, line, outcomes, etc.

    Returns
    -------
    list[MarketCurrentWrite]
        One entry per input market, with changed=True/False indicating whether
        the market needs to be written to history table.
    """
    from src.storage.write_queue import MarketCurrentWrite

    result: list[MarketCurrentWrite] = []

    for event_id, bookmaker_slug, markets_data in markets:
        # Get cached snapshot for this event+bookmaker
        cached_markets: tuple[CachedMarket, ...] | None = None

        if bookmaker_slug == "betpawa":
            # BetPawa uses bookmaker_id=1
            by_bookmaker = cache.get_betpawa_snapshot(event_id)
            if by_bookmaker is not None:
                # Get first bookmaker's snapshot (typically only one)
                for cached_snap in by_bookmaker.values():
                    cached_markets = cached_snap.markets
                    break
        else:
            # Competitors use source string (sportybet, bet9ja)
            by_source = cache.get_competitor_snapshot(event_id)
            if by_source is not None:
                cached_snap = by_source.get(bookmaker_slug)
                if cached_snap is not None:
                    cached_markets = cached_snap.markets

        # Build lookup for cached markets by (betpawa_market_id, line)
        cached_lookup: dict[tuple[str, float | None], CachedMarket] = {}
        if cached_markets is not None:
            for cm in cached_markets:
                key = (cm.betpawa_market_id, cm.line)
                cached_lookup[key] = cm

        # Process each market in the input
        for market in markets_data:
            # Support both ORM objects and dicts
            if isinstance(market, dict):
                market_id = str(market.get("betpawa_market_id", ""))
                market_name = str(market.get("betpawa_market_name", ""))
                line = market.get("line")
                handicap_type = market.get("handicap_type")
                handicap_home = market.get("handicap_home")
                handicap_away = market.get("handicap_away")
                outcomes = market.get("outcomes", [])
                market_groups = market.get("market_groups")
                unavailable_at = market.get("unavailable_at")
            else:
                market_id = str(market.betpawa_market_id)
                market_name = str(getattr(market, "betpawa_market_name", ""))
                line = market.line
                handicap_type = getattr(market, "handicap_type", None)
                handicap_home = getattr(market, "handicap_home", None)
                handicap_away = getattr(market, "handicap_away", None)
                outcomes = market.outcomes if isinstance(market.outcomes, list) else []
                market_groups = getattr(market, "market_groups", None)
                unavailable_at = getattr(market, "unavailable_at", None)

            # Check if this specific market changed
            key = (market_id, line)
            cached_market = cached_lookup.get(key)

            if cached_market is None:
                # New market - not in cache
                changed = True
            else:
                # Compare outcomes
                cached_outcomes = _normalise_outcomes(cached_market.outcomes)
                new_outcomes = _normalise_outcomes(outcomes)
                changed = cached_outcomes != new_outcomes

            # Build MarketCurrentWrite
            write = MarketCurrentWrite(
                event_id=event_id,
                bookmaker_slug=bookmaker_slug,
                betpawa_market_id=market_id,
                betpawa_market_name=market_name,
                line=line,
                handicap_type=handicap_type,
                handicap_home=handicap_home,
                handicap_away=handicap_away,
                outcomes=outcomes,
                market_groups=market_groups,
                unavailable_at=unavailable_at,
                changed=changed,
            )
            result.append(write)

    logger.debug(
        "change_detection.classify_market_changes",
        total_markets=len(result),
        changed_count=sum(1 for m in result if m.changed),
        unchanged_count=sum(1 for m in result if not m.changed),
    )

    return result
