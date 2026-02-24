"""Startup warmup: pre-populate OddsCache from the database.

Loads the latest betpawa and competitor snapshots for upcoming events
(kickoff > now - 2 hours) so the API can serve them from memory instead
of running expensive GROUP BY queries on every request.

Warmup Flow:
    1. Query Event.id where kickoff > cutoff (upcoming events)
    2. Subquery: MAX(OddsSnapshot.id) GROUP BY event_id, bookmaker_id
    3. Join to get full snapshots with selectinload(markets)
    4. Convert to CachedSnapshot and populate cache
    5. Repeat for CompetitorOddsSnapshot via CompetitorEvent link

Conversion Helpers:
    snapshot_to_cached(): Convert ORM snapshot to CachedSnapshot
    snapshot_to_cached_from_models(): Convert in-memory ORM objects
    snapshot_to_cached_from_data(): Convert MarketWriteData DTOs

Usage:
    # In FastAPI lifespan
    async with async_session_factory() as db:
        stats = await warm_cache_from_db(cache, db)
        logger.info("Cache warmed", **stats)

Performance:
    Typical warmup: ~200-500ms for 500 events with 50 markets each.
    Run once at startup; incremental updates via EventCoordinator.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.caching.odds_cache import CachedMarket, CachedSnapshot, OddsCache
from src.db.models.bookmaker import Bookmaker
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorOddsSnapshot,
)
from src.db.models.event import Event
from src.db.models.market_odds import MarketOddsCurrent
from src.db.models.odds import OddsSnapshot

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def snapshot_to_cached_from_data(
    snapshot_id: int,
    event_id: int,
    bookmaker_id: int,
    captured_at: datetime,
    last_confirmed_at: datetime,
    markets: tuple,
) -> CachedSnapshot:
    """Convert write-data DTO market tuples to a CachedSnapshot.

    Similar to ``snapshot_to_cached_from_models`` but accepts frozen-dataclass
    ``MarketWriteData`` objects (from ``src.storage.write_queue``) instead of
    ORM model instances.  Used by the EventCoordinator to update the cache
    immediately after scraping — before the write queue persists to DB.

    Parameters
    ----------
    snapshot_id:
        Row ID (0 for changed snapshots whose real ID is not yet assigned).
    event_id:
        The betpawa event_id.
    bookmaker_id:
        The bookmaker_id (0 for competitor snapshots).
    captured_at:
        Timestamp for when the snapshot was captured.
    last_confirmed_at:
        Timestamp for when the odds were last verified (for freshness display).
    markets:
        Tuple of ``MarketWriteData`` frozen dataclasses.
    """
    cached_markets: list[CachedMarket] = []
    for m in markets:
        cached_markets.append(
            CachedMarket(
                betpawa_market_id=m.betpawa_market_id,
                betpawa_market_name=m.betpawa_market_name,
                line=m.line,
                handicap_type=m.handicap_type,
                handicap_home=m.handicap_home,
                handicap_away=m.handicap_away,
                outcomes=m.outcomes if isinstance(m.outcomes, list) else [],
                market_groups=m.market_groups,
                unavailable_at=getattr(m, "unavailable_at", None),
            )
        )

    return CachedSnapshot(
        snapshot_id=snapshot_id,
        event_id=event_id,
        bookmaker_id=bookmaker_id,
        captured_at=captured_at,
        last_confirmed_at=last_confirmed_at,
        markets=tuple(cached_markets),
    )


def snapshot_to_cached_from_models(
    snapshot_id: int,
    event_id: int,
    bookmaker_id: int,
    captured_at: datetime,
    last_confirmed_at: datetime,
    markets: list,
) -> CachedSnapshot:
    """Convert in-memory ORM model data to a CachedSnapshot.

    Works with ORM model objects that have been flushed (IDs assigned) but
    not necessarily committed.  Accepts the market list directly so it works
    with both ``MarketOdds`` and ``CompetitorMarketOdds`` instances.

    Parameters
    ----------
    snapshot_id:
        The snapshot row ID (populated after flush).
    event_id:
        The betpawa event_id to store on the cached snapshot.
    bookmaker_id:
        The bookmaker_id (0 for competitor snapshots).
    captured_at:
        When the snapshot was captured.
    last_confirmed_at:
        When the odds were last verified (for freshness display).
    markets:
        List of MarketOdds or CompetitorMarketOdds ORM objects.
    """
    cached_markets: list[CachedMarket] = []
    for m in markets:
        cached_markets.append(
            CachedMarket(
                betpawa_market_id=m.betpawa_market_id,
                betpawa_market_name=m.betpawa_market_name,
                line=m.line,
                handicap_type=getattr(m, "handicap_type", None),
                handicap_home=getattr(m, "handicap_home", None),
                handicap_away=getattr(m, "handicap_away", None),
                outcomes=m.outcomes if isinstance(m.outcomes, list) else [],
                market_groups=getattr(m, "market_groups", None),
                unavailable_at=getattr(m, "unavailable_at", None),
            )
        )

    return CachedSnapshot(
        snapshot_id=snapshot_id,
        event_id=event_id,
        bookmaker_id=bookmaker_id,
        captured_at=captured_at,
        last_confirmed_at=last_confirmed_at,
        markets=tuple(cached_markets),
    )


def snapshot_to_cached(
    snapshot: OddsSnapshot | CompetitorOddsSnapshot,
    *,
    event_id: int | None = None,
    bookmaker_id: int = 0,
) -> CachedSnapshot:
    """Convert a SQLAlchemy snapshot model to a CachedSnapshot.

    Works for both OddsSnapshot (has .event_id, .bookmaker_id) and
    CompetitorOddsSnapshot (has .competitor_event_id).

    Parameters
    ----------
    snapshot:
        The ORM snapshot object (must have .markets eagerly loaded).
    event_id:
        The betpawa event_id to store on the cached snapshot.  For
        OddsSnapshot this is read from the model; for CompetitorOddsSnapshot
        the caller must supply it (the betpawa_event_id from CompetitorEvent).
    bookmaker_id:
        The bookmaker_id.  For OddsSnapshot this is read from the model;
        for CompetitorOddsSnapshot it defaults to 0.
    """
    # Resolve event_id and bookmaker_id from the model when available
    if isinstance(snapshot, OddsSnapshot):
        resolved_event_id = snapshot.event_id
        resolved_bookmaker_id = snapshot.bookmaker_id
    else:
        # CompetitorOddsSnapshot -- caller provides event_id
        resolved_event_id = event_id if event_id is not None else 0
        resolved_bookmaker_id = bookmaker_id

    cached_markets: list[CachedMarket] = []
    for m in snapshot.markets:
        cached_markets.append(
            CachedMarket(
                betpawa_market_id=m.betpawa_market_id,
                betpawa_market_name=m.betpawa_market_name,
                line=m.line,
                handicap_type=m.handicap_type,
                handicap_home=m.handicap_home,
                handicap_away=m.handicap_away,
                outcomes=m.outcomes if isinstance(m.outcomes, list) else [],
                market_groups=m.market_groups,
                unavailable_at=getattr(m, "unavailable_at", None),
            )
        )

    # Use last_confirmed_at if available, fall back to captured_at for old data
    last_confirmed = getattr(snapshot, "last_confirmed_at", None) or snapshot.captured_at

    return CachedSnapshot(
        snapshot_id=snapshot.id,
        event_id=resolved_event_id,
        bookmaker_id=resolved_bookmaker_id,
        captured_at=snapshot.captured_at,
        last_confirmed_at=last_confirmed,
        markets=tuple(cached_markets),
    )


# ---------------------------------------------------------------------------
# Warmup entry-point
# ---------------------------------------------------------------------------


async def warm_cache_from_db(cache: OddsCache, db: AsyncSession) -> dict:
    """Load latest market odds for upcoming events from DB into cache.

    Uses the new market_odds_current table for simplified queries (no GROUP BY).
    Returns a dict with warmup statistics.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # DB stores naive UTC
    cutoff = now - timedelta(hours=2)

    # ------------------------------------------------------------------
    # 1. Fetch upcoming BetPawa event IDs + kickoffs
    # ------------------------------------------------------------------
    event_rows = await db.execute(
        select(Event.id, Event.kickoff).where(Event.kickoff > cutoff)
    )
    events = event_rows.all()
    event_ids = [row.id for row in events]
    kickoff_map: dict[int, datetime] = {row.id: row.kickoff for row in events}

    if not event_ids:
        logger.info("cache.warmup.no_events", cutoff=cutoff.isoformat())
        return {"betpawa_snapshots": 0, "competitor_snapshots": 0, "events": 0}

    # ------------------------------------------------------------------
    # 2. Load bookmaker slug -> ID mapping
    # ------------------------------------------------------------------
    bookmaker_result = await db.execute(select(Bookmaker))
    bookmakers = bookmaker_result.scalars().all()
    bookmaker_id_map: dict[str, int] = {b.slug: b.id for b in bookmakers}

    # ------------------------------------------------------------------
    # 3. Load from market_odds_current (all bookmakers in one query)
    # ------------------------------------------------------------------
    moc_query = select(MarketOddsCurrent).where(
        MarketOddsCurrent.event_id.in_(event_ids)
    )
    moc_result = await db.execute(moc_query)
    all_markets = moc_result.scalars().all()

    # Group markets by (event_id, bookmaker_slug)
    # Key: (event_id, bookmaker_slug) -> list of MarketOddsCurrent
    markets_by_event_bookmaker: dict[tuple[int, str], list[MarketOddsCurrent]] = (
        defaultdict(list)
    )
    for market in all_markets:
        key = (market.event_id, market.bookmaker_slug)
        markets_by_event_bookmaker[key].append(market)

    # ------------------------------------------------------------------
    # 3. Build CachedSnapshots and populate cache
    # ------------------------------------------------------------------
    betpawa_count = 0
    competitor_count = 0

    for (event_id, bookmaker_slug), markets in markets_by_event_bookmaker.items():
        if not markets:
            continue

        # Build CachedMarket list from MarketOddsCurrent rows
        cached_markets: list[CachedMarket] = []
        for m in markets:
            cached_markets.append(
                CachedMarket(
                    betpawa_market_id=m.betpawa_market_id,
                    betpawa_market_name=m.betpawa_market_name,
                    line=m.line,
                    handicap_type=m.handicap_type,
                    handicap_home=m.handicap_home,
                    handicap_away=m.handicap_away,
                    outcomes=m.outcomes if isinstance(m.outcomes, list) else [],
                    market_groups=m.market_groups,
                    unavailable_at=m.unavailable_at,
                )
            )

        # Use max timestamps across all markets in this group
        # Handle timezone-aware datetimes from database
        last_updated = max(
            (m.last_updated_at.replace(tzinfo=None) if m.last_updated_at.tzinfo else m.last_updated_at)
            for m in markets
        )
        last_confirmed = max(
            (m.last_confirmed_at.replace(tzinfo=None) if m.last_confirmed_at.tzinfo else m.last_confirmed_at)
            for m in markets
        )

        cached_snapshot = CachedSnapshot(
            snapshot_id=0,  # Not used in new schema
            event_id=event_id,
            bookmaker_id=bookmaker_id_map.get(bookmaker_slug, 0),
            captured_at=last_updated,
            last_confirmed_at=last_confirmed,
            markets=tuple(cached_markets),
        )

        kickoff = kickoff_map.get(event_id)

        if bookmaker_slug == "betpawa":
            # BetPawa snapshot - use actual bookmaker_id from DB
            bp_bookmaker_id = bookmaker_id_map.get("betpawa", 1)
            cache.put_betpawa_snapshot(
                event_id=event_id,
                bookmaker_id=bp_bookmaker_id,
                snapshot=cached_snapshot,
                kickoff=kickoff,
            )
            betpawa_count += 1
        else:
            # Competitor snapshot (sportybet or bet9ja)
            cache.put_competitor_snapshot(
                event_id=event_id,
                source=bookmaker_slug,
                snapshot=cached_snapshot,
                kickoff=kickoff,
            )
            competitor_count += 1

    stats = cache.stats()
    logger.info(
        "cache.warmup.complete",
        events=len(event_ids),
        betpawa_snapshots=betpawa_count,
        competitor_snapshots=competitor_count,
        **stats,
    )

    return {
        "events": len(event_ids),
        "betpawa_snapshots": betpawa_count,
        "competitor_snapshots": competitor_count,
        **stats,
    }
