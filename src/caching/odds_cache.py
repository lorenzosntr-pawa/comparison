"""In-memory cache for odds snapshots, replacing expensive GROUP BY queries.

Stores the latest odds per event/bookmaker in plain frozen dataclasses to
avoid SQLAlchemy detached-instance issues. Thread-safe for single-writer /
multi-reader asyncio usage (GIL protects dict mutations).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

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

    def evict_expired(self, cutoff: datetime) -> int:
        """Remove events whose kickoff is before *cutoff*.

        Returns the number of events evicted.
        """
        expired_ids = [
            eid for eid, ko in self._event_kickoffs.items() if ko < cutoff
        ]
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
        """Return summary statistics about the cache contents."""
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

        return {
            "betpawa_events": betpawa_events,
            "competitor_events": competitor_events,
            "total_snapshots": total_snapshots,
            "total_markets": total_markets,
        }
