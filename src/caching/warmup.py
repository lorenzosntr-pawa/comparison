"""Startup warmup: pre-populate OddsCache from the database.

Loads the latest betpawa and competitor snapshots for upcoming events
(kickoff > now - 2 hours) so the API can serve them from memory instead
of running expensive GROUP BY queries on every request.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.caching.odds_cache import CachedMarket, CachedSnapshot, OddsCache
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorOddsSnapshot,
)
from src.db.models.event import Event
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
    """Load latest snapshots for upcoming events from DB into cache.

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
    # 2. Load latest BetPawa snapshots (same GROUP BY as events.py)
    # ------------------------------------------------------------------
    latest_bp_subq = (
        select(
            OddsSnapshot.event_id,
            OddsSnapshot.bookmaker_id,
            func.max(OddsSnapshot.id).label("max_id"),
        )
        .where(OddsSnapshot.event_id.in_(event_ids))
        .group_by(OddsSnapshot.event_id, OddsSnapshot.bookmaker_id)
        .subquery()
    )

    bp_query = (
        select(OddsSnapshot)
        .join(
            latest_bp_subq,
            (OddsSnapshot.event_id == latest_bp_subq.c.event_id)
            & (OddsSnapshot.bookmaker_id == latest_bp_subq.c.bookmaker_id)
            & (OddsSnapshot.id == latest_bp_subq.c.max_id),
        )
        .options(selectinload(OddsSnapshot.markets))
    )

    bp_result = await db.execute(bp_query)
    bp_snapshots = bp_result.scalars().all()

    betpawa_count = 0
    for snap in bp_snapshots:
        cached = snapshot_to_cached(snap)
        cache.put_betpawa_snapshot(
            event_id=snap.event_id,
            bookmaker_id=snap.bookmaker_id,
            snapshot=cached,
            kickoff=kickoff_map.get(snap.event_id),
        )
        betpawa_count += 1

    # ------------------------------------------------------------------
    # 3. Load latest competitor snapshots
    # ------------------------------------------------------------------
    comp_events_result = await db.execute(
        select(CompetitorEvent).where(
            CompetitorEvent.betpawa_event_id.in_(event_ids)
        )
    )
    comp_events = comp_events_result.scalars().all()

    competitor_count = 0
    if comp_events:
        comp_event_ids = [ce.id for ce in comp_events]

        latest_comp_subq = (
            select(
                CompetitorOddsSnapshot.competitor_event_id,
                func.max(CompetitorOddsSnapshot.id).label("max_id"),
            )
            .where(CompetitorOddsSnapshot.competitor_event_id.in_(comp_event_ids))
            .group_by(CompetitorOddsSnapshot.competitor_event_id)
            .subquery()
        )

        comp_snap_query = (
            select(CompetitorOddsSnapshot)
            .join(
                latest_comp_subq,
                (CompetitorOddsSnapshot.competitor_event_id == latest_comp_subq.c.competitor_event_id)
                & (CompetitorOddsSnapshot.id == latest_comp_subq.c.max_id),
            )
            .options(selectinload(CompetitorOddsSnapshot.markets))
        )

        comp_snap_result = await db.execute(comp_snap_query)
        comp_snapshots = comp_snap_result.scalars().all()

        # Build lookup: competitor_event_id -> snapshot
        snap_by_ce_id = {s.competitor_event_id: s for s in comp_snapshots}

        for ce in comp_events:
            snap = snap_by_ce_id.get(ce.id)
            if snap and ce.betpawa_event_id is not None:
                cached = snapshot_to_cached(
                    snap,
                    event_id=ce.betpawa_event_id,
                )
                cache.put_competitor_snapshot(
                    event_id=ce.betpawa_event_id,
                    source=ce.source,
                    snapshot=cached,
                    kickoff=kickoff_map.get(ce.betpawa_event_id),
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
