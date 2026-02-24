"""Historical data API endpoints for odds and margin history.

Updated in Phase 109 to use market_odds_history table.
Updated in Phase 110.1 to also query legacy tables for pre-v2.9 data (BUG-028 fix).

This module implements a dual-query strategy:
1. Query new market_odds_history (post-v2.9 data)
2. Query legacy odds_snapshots + market_odds tables (pre-v2.9 data)
3. UNION results for complete historical coverage
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_db
from src.db.models.bookmaker import Bookmaker
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
)
from src.db.models.market_odds import MarketOddsHistory
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.matching.schemas import (
    MarginHistoryPoint,
    MarginHistoryResponse,
    OddsHistoryPoint,
    OddsHistoryResponse,
    OutcomeOdds,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/events", tags=["history"])


def _calculate_margin_from_outcomes(outcomes: list) -> float | None:
    """Calculate margin from JSONB outcomes array.

    Margin = (sum(1/odds) - 1) * 100

    Args:
        outcomes: List of outcome dicts with 'odds' field.

    Returns:
        Margin as percentage, or None if calculation not possible.
    """
    if not outcomes:
        return None
    try:
        total_implied = sum(1.0 / o["odds"] for o in outcomes if o.get("odds", 0) > 0)
        if total_implied == 0:
            return None
        return round((total_implied - 1) * 100, 2)
    except (KeyError, TypeError, ZeroDivisionError):
        return None


# Note: get_snapshot_history endpoint removed in Phase 109 (v2.9)
# The snapshot concept no longer exists with market-level storage.
# Frontend uses /markets/{id}/history and /markets/{id}/margin-history instead.


async def _query_legacy_betpawa_history(
    db: AsyncSession,
    event_id: int,
    market_id: str,
    line: float | None,
    from_time: datetime | None,
    to_time: datetime | None,
) -> list[dict[str, Any]]:
    """Query legacy odds_snapshots + market_odds for BetPawa pre-v2.9 data.

    Returns list of dicts with captured_at, outcomes, line for consistency.
    """
    query = (
        select(MarketOdds, OddsSnapshot.captured_at)
        .join(OddsSnapshot, MarketOdds.snapshot_id == OddsSnapshot.id)
        .where(OddsSnapshot.event_id == event_id)
        .where(MarketOdds.betpawa_market_id == market_id)
    )

    # Apply line filter
    if line is not None:
        query = query.where(MarketOdds.line == line)

    # Apply time filters
    if from_time:
        from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
        query = query.where(OddsSnapshot.captured_at >= from_time_naive)
    if to_time:
        to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
        query = query.where(OddsSnapshot.captured_at <= to_time_naive)

    query = query.order_by(OddsSnapshot.captured_at)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "captured_at": row.captured_at,
            "outcomes": row.MarketOdds.outcomes,
            "line": row.MarketOdds.line,
            "unavailable_at": getattr(row.MarketOdds, "unavailable_at", None),
        }
        for row in rows
    ]


async def _query_legacy_competitor_history(
    db: AsyncSession,
    event_id: int,
    bookmaker_slug: str,
    market_id: str,
    line: float | None,
    from_time: datetime | None,
    to_time: datetime | None,
) -> list[dict[str, Any]]:
    """Query legacy competitor_odds_snapshots + competitor_market_odds for pre-v2.9 data.

    Returns list of dicts with captured_at, outcomes, line for consistency.
    """
    query = (
        select(CompetitorMarketOdds, CompetitorOddsSnapshot.captured_at)
        .join(
            CompetitorOddsSnapshot,
            CompetitorMarketOdds.snapshot_id == CompetitorOddsSnapshot.id,
        )
        .join(
            CompetitorEvent,
            CompetitorOddsSnapshot.competitor_event_id == CompetitorEvent.id,
        )
        .where(CompetitorEvent.betpawa_event_id == event_id)
        .where(CompetitorEvent.source == bookmaker_slug)
        .where(CompetitorMarketOdds.betpawa_market_id == market_id)
    )

    # Apply line filter
    if line is not None:
        query = query.where(CompetitorMarketOdds.line == line)

    # Apply time filters
    if from_time:
        from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
        query = query.where(CompetitorOddsSnapshot.captured_at >= from_time_naive)
    if to_time:
        to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
        query = query.where(CompetitorOddsSnapshot.captured_at <= to_time_naive)

    query = query.order_by(CompetitorOddsSnapshot.captured_at)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "captured_at": row.captured_at,
            "outcomes": row.CompetitorMarketOdds.outcomes,
            "line": row.CompetitorMarketOdds.line,
            "unavailable_at": getattr(row.CompetitorMarketOdds, "unavailable_at", None),
        }
        for row in rows
    ]


@router.get("/{event_id}/markets/{market_id}/history", response_model=OddsHistoryResponse)
async def get_odds_history(
    event_id: int,
    market_id: str,
    db: AsyncSession = Depends(get_db),
    bookmaker_slug: str = Query(
        ...,
        description="Bookmaker slug (required) - e.g., 'betpawa', 'sportybet', 'bet9ja'",
    ),
    from_time: datetime | None = Query(
        default=None,
        description="Start of time range (inclusive)",
    ),
    to_time: datetime | None = Query(
        default=None,
        description="End of time range (inclusive)",
    ),
    line: float | None = Query(
        default=None,
        description="Filter by line value for specifier markets (e.g., 2.5 for Over/Under 2.5)",
    ),
) -> OddsHistoryResponse:
    """Get odds time-series for a specific market.

    Returns chronological odds history with margin calculations for each point.
    Ordered by captured_at ASC for chart consumption. Use this endpoint for
    detailed odds movement visualization including individual outcome odds.

    Updated in Phase 109 to use market_odds_history table with unified
    bookmaker handling via bookmaker_slug field.

    Args:
        event_id: BetPawa event ID.
        market_id: BetPawa market ID (e.g., "3743" for 1X2).
        db: Async database session (injected).
        bookmaker_slug: Required bookmaker slug (betpawa, sportybet, bet9ja).
        from_time: Optional start of time range (inclusive).
        to_time: Optional end of time range (inclusive).
        line: Optional line value for specifier markets (e.g., 2.5 for Over/Under).

    Returns:
        OddsHistoryResponse with chronological odds history and margin data.

    Raises:
        HTTPException: 404 if bookmaker not found.
    """
    # Validate bookmaker exists
    bookmaker_result = await db.execute(
        select(Bookmaker).where(Bookmaker.slug == bookmaker_slug)
    )
    bookmaker = bookmaker_result.scalar_one_or_none()
    if not bookmaker:
        raise HTTPException(status_code=404, detail=f"Bookmaker not found: {bookmaker_slug}")

    # =========================================================================
    # DUAL-QUERY STRATEGY (Phase 110.1 - BUG-028 fix)
    # Query BOTH new market_odds_history AND legacy tables to get complete history
    # =========================================================================

    all_points: list[dict[str, Any]] = []

    # 1. Query new market_odds_history (post-v2.9 data)
    query = (
        select(MarketOddsHistory)
        .where(MarketOddsHistory.event_id == event_id)
        .where(MarketOddsHistory.bookmaker_slug == bookmaker_slug)
        .where(MarketOddsHistory.betpawa_market_id == market_id)
    )

    if line is not None:
        query = query.where(MarketOddsHistory.line == line)

    if from_time:
        from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
        query = query.where(MarketOddsHistory.captured_at >= from_time_naive)
    if to_time:
        to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
        query = query.where(MarketOddsHistory.captured_at <= to_time_naive)

    result = await db.execute(query)
    for market in result.scalars().all():
        all_points.append({
            "captured_at": market.captured_at,
            "outcomes": market.outcomes,
            "line": market.line,
            "unavailable_at": None,  # New table doesn't track this per-row
        })

    # 2. Query legacy tables (pre-v2.9 data)
    if bookmaker_slug == "betpawa":
        legacy_points = await _query_legacy_betpawa_history(
            db, event_id, market_id, line, from_time, to_time
        )
    else:
        legacy_points = await _query_legacy_competitor_history(
            db, event_id, bookmaker_slug, market_id, line, from_time, to_time
        )
    all_points.extend(legacy_points)

    # 3. Deduplicate by captured_at and sort chronologically
    seen_timestamps: set[datetime] = set()
    unique_points: list[dict[str, Any]] = []
    for point in all_points:
        ts = point["captured_at"]
        if ts not in seen_timestamps:
            seen_timestamps.add(ts)
            unique_points.append(point)

    unique_points.sort(key=lambda p: p["captured_at"])

    # 4. Build OddsHistoryPoint response objects
    history: list[OddsHistoryPoint] = []
    result_line = None

    for point in unique_points:
        if result_line is None:
            result_line = point.get("line")

        outcomes = []
        raw_outcomes = point.get("outcomes", [])
        if isinstance(raw_outcomes, list):
            for outcome in raw_outcomes:
                if isinstance(outcome, dict) and "name" in outcome and "odds" in outcome:
                    outcomes.append(
                        OutcomeOdds(name=outcome["name"], odds=outcome["odds"])
                    )

        margin = _calculate_margin_from_outcomes(
            raw_outcomes if isinstance(raw_outcomes, list) else []
        )

        history.append(
            OddsHistoryPoint(
                captured_at=point["captured_at"],
                outcomes=outcomes,
                margin=margin,
                available=point.get("unavailable_at") is None,
                unavailable_at=point.get("unavailable_at"),
            )
        )

    logger.debug(
        "odds_history_query",
        event_id=event_id,
        market_id=market_id,
        bookmaker_slug=bookmaker_slug,
        points=len(history),
        new_table_points=len([p for p in all_points if p not in legacy_points]),
        legacy_points=len(legacy_points),
    )

    return OddsHistoryResponse(
        event_id=event_id,
        bookmaker_slug=bookmaker.slug,
        bookmaker_name=bookmaker.name,
        market_id=market_id,
        market_name=market_id,
        line=result_line,
        history=history,
    )


@router.get("/{event_id}/markets/{market_id}/margin-history", response_model=MarginHistoryResponse)
async def get_margin_history(
    event_id: int,
    market_id: str,
    db: AsyncSession = Depends(get_db),
    bookmaker_slug: str = Query(
        ...,
        description="Bookmaker slug (required) - e.g., 'betpawa', 'sportybet', 'bet9ja'",
    ),
    from_time: datetime | None = Query(
        default=None,
        description="Start of time range (inclusive)",
    ),
    to_time: datetime | None = Query(
        default=None,
        description="End of time range (inclusive)",
    ),
    line: float | None = Query(
        default=None,
        description="Filter by line value for specifier markets (e.g., 2.5 for Over/Under 2.5)",
    ),
) -> MarginHistoryResponse:
    """Get margin-only time-series for a specific market.

    Returns a lighter response with just timestamps and margins (no outcomes).
    Ordered by captured_at ASC for chart consumption. Use this endpoint for
    margin-only charts where individual outcome odds are not needed.

    Updated in Phase 109 to use market_odds_history table with unified
    bookmaker handling via bookmaker_slug field.

    Args:
        event_id: BetPawa event ID.
        market_id: BetPawa market ID (e.g., "3743" for 1X2).
        db: Async database session (injected).
        bookmaker_slug: Required bookmaker slug (betpawa, sportybet, bet9ja).
        from_time: Optional start of time range (inclusive).
        to_time: Optional end of time range (inclusive).
        line: Optional line value for specifier markets (e.g., 2.5 for Over/Under).

    Returns:
        MarginHistoryResponse with chronological margin data only.

    Raises:
        HTTPException: 404 if bookmaker not found.
    """
    # Validate bookmaker exists
    bookmaker_result = await db.execute(
        select(Bookmaker).where(Bookmaker.slug == bookmaker_slug)
    )
    bookmaker = bookmaker_result.scalar_one_or_none()
    if not bookmaker:
        raise HTTPException(status_code=404, detail=f"Bookmaker not found: {bookmaker_slug}")

    # =========================================================================
    # DUAL-QUERY STRATEGY (Phase 110.1 - BUG-028 fix)
    # Query BOTH new market_odds_history AND legacy tables to get complete history
    # =========================================================================

    all_points: list[dict[str, Any]] = []

    # 1. Query new market_odds_history (post-v2.9 data)
    query = (
        select(MarketOddsHistory)
        .where(MarketOddsHistory.event_id == event_id)
        .where(MarketOddsHistory.bookmaker_slug == bookmaker_slug)
        .where(MarketOddsHistory.betpawa_market_id == market_id)
    )

    if line is not None:
        query = query.where(MarketOddsHistory.line == line)

    if from_time:
        from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
        query = query.where(MarketOddsHistory.captured_at >= from_time_naive)
    if to_time:
        to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
        query = query.where(MarketOddsHistory.captured_at <= to_time_naive)

    result = await db.execute(query)
    for market in result.scalars().all():
        all_points.append({
            "captured_at": market.captured_at,
            "outcomes": market.outcomes,
            "line": market.line,
            "unavailable_at": None,
        })

    # 2. Query legacy tables (pre-v2.9 data)
    if bookmaker_slug == "betpawa":
        legacy_points = await _query_legacy_betpawa_history(
            db, event_id, market_id, line, from_time, to_time
        )
    else:
        legacy_points = await _query_legacy_competitor_history(
            db, event_id, bookmaker_slug, market_id, line, from_time, to_time
        )
    all_points.extend(legacy_points)

    # 3. Deduplicate by captured_at and sort chronologically
    seen_timestamps: set[datetime] = set()
    unique_points: list[dict[str, Any]] = []
    for point in all_points:
        ts = point["captured_at"]
        if ts not in seen_timestamps:
            seen_timestamps.add(ts)
            unique_points.append(point)

    unique_points.sort(key=lambda p: p["captured_at"])

    # 4. Build MarginHistoryPoint response objects
    history: list[MarginHistoryPoint] = []
    result_line = None

    for point in unique_points:
        if result_line is None:
            result_line = point.get("line")

        raw_outcomes = point.get("outcomes", [])
        margin = _calculate_margin_from_outcomes(
            raw_outcomes if isinstance(raw_outcomes, list) else []
        )

        history.append(
            MarginHistoryPoint(
                captured_at=point["captured_at"],
                margin=margin,
                available=point.get("unavailable_at") is None,
                unavailable_at=point.get("unavailable_at"),
            )
        )

    logger.debug(
        "margin_history_query",
        event_id=event_id,
        market_id=market_id,
        bookmaker_slug=bookmaker_slug,
        points=len(history),
        new_table_points=len([p for p in all_points if p not in legacy_points]),
        legacy_points=len(legacy_points),
    )

    return MarginHistoryResponse(
        event_id=event_id,
        bookmaker_slug=bookmaker.slug,
        bookmaker_name=bookmaker.name,
        market_id=market_id,
        market_name=market_id,
        line=result_line,
        history=history,
    )
