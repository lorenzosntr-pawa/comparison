"""In-memory cache for odds snapshots, replacing expensive GROUP BY queries.

Stores the latest odds per event/bookmaker in plain frozen dataclasses to
avoid SQLAlchemy detached-instance issues. Thread-safe for single-writer /
multi-reader asyncio usage (GIL protects dict mutations).

Data Structures:
    CachedMarket: Frozen dataclass mirroring MarketOdds/CompetitorMarketOdds
    CachedSnapshot: Frozen dataclass with snapshot_id, event_id, markets tuple

Internal Layout:
    _betpawa_snapshots: Dict[event_id, Dict[bookmaker_id, CachedSnapshot]]
    _competitor_snapshots: Dict[event_id, Dict[source, CachedSnapshot]]
    _event_kickoffs: Dict[event_id, datetime] for eviction cutoff

Thread Safety:
    Single-writer (EventCoordinator) / multi-reader (API endpoints) safe.
    Dict mutations are atomic under GIL. No explicit locking needed for
    the common put/get patterns.

Callbacks:
    Register on_update callbacks for WebSocket broadcasting:
    cache.on_update(lambda event_ids, source: ws_manager.notify(event_ids))

Memory:
    ~200 bytes per CachedMarket, stats() returns estimated_memory_mb
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Frozen dataclasses -- duck-type compatible with OddsSnapshot / MarketOdds
# and CompetitorOddsSnapshot / CompetitorMarketOdds
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CachedMarket:
    """Immutable market data mirroring MarketOdds / CompetitorMarketOdds.

    Attributes are named to match the SQLAlchemy model attributes so that
    ``_build_inline_odds()`` and ``_build_competitor_inline_odds()`` in
    ``src/api/routes/events.py`` can consume CachedSnapshot.markets without
    any code changes.
    """

    betpawa_market_id: str
    betpawa_market_name: str
    line: float | None
    handicap_type: str | None
    handicap_home: float | None
    handicap_away: float | None
    outcomes: list[dict]  # [{name, odds, is_active}, ...]
    market_groups: list[str] | None


@dataclass(frozen=True)
class CachedSnapshot:
    """Immutable odds snapshot mirroring OddsSnapshot / CompetitorOddsSnapshot.

    Duck-type compatible with both OddsSnapshot (has event_id, bookmaker_id)
    and CompetitorOddsSnapshot (has competitor_event_id).  The functions in
    events.py only access ``.markets`` and each market's attribute names, so
    this works as a drop-in replacement for both model types.
    """

    snapshot_id: int
    event_id: int
    bookmaker_id: int
    captured_at: datetime
    last_confirmed_at: datetime  # When odds were last verified (for freshness display)
    markets: tuple[CachedMarket, ...]  # tuple for immutability


# ---------------------------------------------------------------------------
# OddsCache
# ---------------------------------------------------------------------------


class OddsCache:
    """In-memory cache of latest odds snapshots keyed by event.

    Designed to be instantiated once and stored on ``app.state``.

    Internal layout
    ---------------
    * ``_betpawa_snapshots``   : event_id -> bookmaker_id -> CachedSnapshot
    * ``_competitor_snapshots`` : event_id -> source       -> CachedSnapshot
    * ``_event_kickoffs``      : event_id -> kickoff datetime (for eviction)
    """

    def __init__(self) -> None:
        self._betpawa_snapshots: dict[int, dict[int, CachedSnapshot]] = {}
        self._competitor_snapshots: dict[int, dict[str, CachedSnapshot]] = {}
        self._event_kickoffs: dict[int, datetime] = {}
        self._on_update_callbacks: list[Callable[[list[int], str], None]] = []

    # -- Callback registration ------------------------------------------------

    def on_update(self, callback: Callable[[list[int], str], None]) -> None:
        """Register a callback for odds updates.

        Callback signature: (event_ids: list[int], source: str) -> None
        - event_ids: list of event IDs that were updated
        - source: "betpawa", "sportybet", or "bet9ja"

        The callback is synchronous (not async) because put_*_snapshot methods
        are sync. The callback should be a thin wrapper that enqueues work for
        async processing -- it must NOT do I/O or await.
        """
        self._on_update_callbacks.append(callback)

    def _notify_update(self, event_ids: list[int], source: str) -> None:
        """Fire all registered update callbacks.

        Errors in one callback do NOT prevent other callbacks from running.
        """
        for cb in self._on_update_callbacks:
            try:
                cb(event_ids, source)
            except Exception:
                logger.exception("cache.on_update.callback_error", source=source)

    # -- Lookup methods (read) ---------------------------------------------

    def get_betpawa_snapshots(
        self, event_ids: list[int]
    ) -> dict[int, dict[int, CachedSnapshot]]:
        """Return betpawa snapshots for the given event IDs.

        Returns the same shape as ``_load_latest_snapshots_for_events()``:
        ``{event_id: {bookmaker_id: CachedSnapshot}}``.
        """
        result: dict[int, dict[int, CachedSnapshot]] = {}
        for eid in event_ids:
            entry = self._betpawa_snapshots.get(eid)
            if entry:
                result[eid] = entry
        return result

    def get_competitor_snapshots(
        self, event_ids: list[int]
    ) -> dict[int, dict[str, CachedSnapshot]]:
        """Return competitor snapshots for the given event IDs.

        Returns the same shape as ``_load_competitor_snapshots_for_events()``:
        ``{event_id: {source: CachedSnapshot}}``.
        """
        result: dict[int, dict[str, CachedSnapshot]] = {}
        for eid in event_ids:
            entry = self._competitor_snapshots.get(eid)
            if entry:
                result[eid] = entry
        return result

    def get_betpawa_snapshot(
        self, event_id: int
    ) -> dict[int, CachedSnapshot] | None:
        """Return betpawa bookmaker->snapshot dict for a single event, or None."""
        return self._betpawa_snapshots.get(event_id)

    def get_competitor_snapshot(
        self, event_id: int
    ) -> dict[str, CachedSnapshot] | None:
        """Return competitor source->snapshot dict for a single event, or None."""
        return self._competitor_snapshots.get(event_id)

    # -- Mutation methods (write) ------------------------------------------

    def put_betpawa_snapshot(
        self,
        event_id: int,
        bookmaker_id: int,
        snapshot: CachedSnapshot,
        kickoff: datetime | None = None,
    ) -> None:
        """Insert or replace the betpawa snapshot for an event+bookmaker."""
        if event_id not in self._betpawa_snapshots:
            self._betpawa_snapshots[event_id] = {}
        self._betpawa_snapshots[event_id][bookmaker_id] = snapshot
        if kickoff is not None:
            self._event_kickoffs[event_id] = kickoff
        self._notify_update([event_id], "betpawa")

    def put_competitor_snapshot(
        self,
        event_id: int,
        source: str,
        snapshot: CachedSnapshot,
        kickoff: datetime | None = None,
    ) -> None:
        """Insert or replace the competitor snapshot for an event+source."""
        if event_id not in self._competitor_snapshots:
            self._competitor_snapshots[event_id] = {}
        self._competitor_snapshots[event_id][source] = snapshot
        if kickoff is not None:
            self._event_kickoffs[event_id] = kickoff
        self._notify_update([event_id], source)

    def evict_expired(self, cutoff: datetime) -> int:
        """Remove events whose kickoff is before *cutoff*.

        Returns the number of events evicted.
        """
        # Normalize cutoff to naive UTC for comparison (strip timezone if present)
        cutoff_naive = cutoff.replace(tzinfo=None) if cutoff.tzinfo else cutoff

        expired_ids = []
        for eid, ko in self._event_kickoffs.items():
            # Normalize kickoff to naive for comparison (handles both aware and naive)
            ko_naive = ko.replace(tzinfo=None) if ko.tzinfo else ko
            if ko_naive < cutoff_naive:
                expired_ids.append(eid)
        for eid in expired_ids:
            self._betpawa_snapshots.pop(eid, None)
            self._competitor_snapshots.pop(eid, None)
            self._event_kickoffs.pop(eid, None)
        if expired_ids:
            logger.info(
                "cache.evict_expired",
                evicted=len(expired_ids),
                cutoff=cutoff.isoformat(),
            )
        return len(expired_ids)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._betpawa_snapshots.clear()
        self._competitor_snapshots.clear()
        self._event_kickoffs.clear()
        logger.info("cache.cleared")

    # -- Stats -------------------------------------------------------------

    def stats(self) -> dict:
        """Return summary statistics about the cache contents.

        Includes an estimated memory usage based on ~200 bytes per cached
        market (frozen dataclass with outcome dicts).
        """
        betpawa_events = len(self._betpawa_snapshots)
        competitor_events = len(self._competitor_snapshots)

        total_snapshots = 0
        total_markets = 0
        for by_bm in self._betpawa_snapshots.values():
            for snap in by_bm.values():
                total_snapshots += 1
                total_markets += len(snap.markets)
        for by_src in self._competitor_snapshots.values():
            for snap in by_src.values():
                total_snapshots += 1
                total_markets += len(snap.markets)

        # Rough memory estimate: ~200 bytes per CachedMarket (frozen dataclass
        # with outcome list, string fields, optional floats) plus ~100 bytes
        # overhead per snapshot and ~50 bytes per dict entry.
        estimated_bytes = (
            total_markets * 200
            + total_snapshots * 100
            + (betpawa_events + competitor_events) * 50
        )
        estimated_memory_mb = round(estimated_bytes / (1024 * 1024), 2)

        return {
            "betpawa_events": betpawa_events,
            "competitor_events": competitor_events,
            "total_snapshots": total_snapshots,
            "total_markets": total_markets,
            "estimated_memory_mb": estimated_memory_mb,
        }
