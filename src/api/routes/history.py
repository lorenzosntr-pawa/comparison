"""Historical data API endpoints for snapshot, odds, and margin history."""

from __future__ import annotations

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_db
from src.db.models.bookmaker import Bookmaker
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
)
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.matching.schemas import (
    HistoricalSnapshot,
    MarginHistoryPoint,
    MarginHistoryResponse,
    OddsHistoryPoint,
    OddsHistoryResponse,
    OutcomeOdds,
    SnapshotHistoryResponse,
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


@router.get("/{event_id}/history", response_model=SnapshotHistoryResponse)
async def get_snapshot_history(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    bookmaker_slug: str | None = Query(
        default=None,
        description="Filter by bookmaker slug (e.g., 'betpawa', 'sportybet', 'bet9ja')",
    ),
    from_time: datetime | None = Query(
        default=None,
        description="Start of time range (inclusive)",
    ),
    to_time: datetime | None = Query(
        default=None,
        description="End of time range (inclusive)",
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(
        default=100, ge=1, le=500, description="Results per page (max 500)"
    ),
) -> SnapshotHistoryResponse:
    """Get historical snapshots for an event.

    Returns a paginated list of snapshots with market counts, ordered by
    captured_at descending (most recent first). Useful for browsing
    available historical data and selecting specific snapshots for analysis.

    Args:
        event_id: BetPawa event ID to get history for.
        db: Async database session (injected).
        bookmaker_slug: Optional filter by bookmaker (betpawa, sportybet, bet9ja).
        from_time: Optional start of time range (inclusive).
        to_time: Optional end of time range (inclusive).
        page: Page number for pagination (default 1).
        page_size: Results per page (1-500, default 100).

    Returns:
        SnapshotHistoryResponse with paginated snapshots and total count.

    Raises:
        HTTPException: 404 if bookmaker_slug is invalid.
    """
    # Subquery to count markets per snapshot
    market_count_subq = (
        select(
            MarketOdds.snapshot_id,
            func.count().label("market_count"),
        )
        .group_by(MarketOdds.snapshot_id)
        .subquery()
    )

    # Base query joining snapshots with bookmakers and market counts
    query = (
        select(
            OddsSnapshot,
            Bookmaker,
            market_count_subq.c.market_count,
        )
        .join(Bookmaker, OddsSnapshot.bookmaker_id == Bookmaker.id)
        .outerjoin(market_count_subq, OddsSnapshot.id == market_count_subq.c.snapshot_id)
        .where(OddsSnapshot.event_id == event_id)
    )

    # Count query for total
    count_query = (
        select(func.count())
        .select_from(OddsSnapshot)
        .where(OddsSnapshot.event_id == event_id)
    )

    # Apply bookmaker filter
    if bookmaker_slug:
        # Get bookmaker ID first
        bookmaker_result = await db.execute(
            select(Bookmaker).where(Bookmaker.slug == bookmaker_slug)
        )
        bookmaker = bookmaker_result.scalar_one_or_none()
        if not bookmaker:
            raise HTTPException(status_code=404, detail=f"Bookmaker not found: {bookmaker_slug}")
        query = query.where(OddsSnapshot.bookmaker_id == bookmaker.id)
        count_query = count_query.where(OddsSnapshot.bookmaker_id == bookmaker.id)

    # Apply time filters (DB stores naive UTC)
    if from_time:
        from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
        query = query.where(OddsSnapshot.captured_at >= from_time_naive)
        count_query = count_query.where(OddsSnapshot.captured_at >= from_time_naive)
    if to_time:
        to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
        query = query.where(OddsSnapshot.captured_at <= to_time_naive)
        count_query = count_query.where(OddsSnapshot.captured_at <= to_time_naive)

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply ordering and pagination
    offset = (page - 1) * page_size
    query = query.order_by(desc(OddsSnapshot.captured_at)).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    rows = result.all()

    # Build response
    snapshots = []
    for row in rows:
        snapshot = row[0]  # OddsSnapshot
        bookmaker = row[1]  # Bookmaker
        market_count = row[2] or 0  # market_count (can be None if no markets)

        snapshots.append(
            HistoricalSnapshot(
                id=snapshot.id,
                captured_at=snapshot.captured_at,
                bookmaker_slug=bookmaker.slug,
                bookmaker_name=bookmaker.name,
                market_count=market_count,
            )
        )

    logger.debug(
        "snapshot_history_query",
        event_id=event_id,
        bookmaker_slug=bookmaker_slug,
        total=total,
        returned=len(snapshots),
        page=page,
    )

    return SnapshotHistoryResponse(
        event_id=event_id,
        snapshots=snapshots,
        total=total,
    )


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
    # Check if this is a competitor bookmaker
    is_competitor = bookmaker_slug in ("sportybet", "bet9ja")

    # Get bookmaker info for response
    bookmaker_result = await db.execute(
        select(Bookmaker).where(Bookmaker.slug == bookmaker_slug)
    )
    bookmaker = bookmaker_result.scalar_one_or_none()
    if not bookmaker:
        raise HTTPException(status_code=404, detail=f"Bookmaker not found: {bookmaker_slug}")

    if is_competitor:
        # Query competitor tables
        # Link CompetitorEvent -> CompetitorOddsSnapshot -> CompetitorMarketOdds
        query = (
            select(CompetitorOddsSnapshot, CompetitorMarketOdds)
            .join(CompetitorEvent, CompetitorOddsSnapshot.competitor_event_id == CompetitorEvent.id)
            .join(CompetitorMarketOdds, CompetitorMarketOdds.snapshot_id == CompetitorOddsSnapshot.id)
            .where(CompetitorEvent.betpawa_event_id == event_id)
            .where(CompetitorEvent.source == bookmaker_slug)
            .where(CompetitorMarketOdds.betpawa_market_id == market_id)
        )

        # Apply line filter for specifier markets
        if line is not None:
            query = query.where(CompetitorMarketOdds.line == line)

        # Apply time filters (DB stores naive UTC)
        if from_time:
            from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
            query = query.where(CompetitorOddsSnapshot.captured_at >= from_time_naive)
        if to_time:
            to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
            query = query.where(CompetitorOddsSnapshot.captured_at <= to_time_naive)

        # Order chronologically for charts
        query = query.order_by(CompetitorOddsSnapshot.captured_at)
    else:
        # Query BetPawa tables (original behavior)
        query = (
            select(OddsSnapshot, MarketOdds)
            .join(MarketOdds, MarketOdds.snapshot_id == OddsSnapshot.id)
            .where(OddsSnapshot.event_id == event_id)
            .where(OddsSnapshot.bookmaker_id == bookmaker.id)
            .where(MarketOdds.betpawa_market_id == market_id)
        )

        # Apply line filter for specifier markets
        if line is not None:
            query = query.where(MarketOdds.line == line)

        # Apply time filters (DB stores naive UTC)
        if from_time:
            from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
            query = query.where(OddsSnapshot.captured_at >= from_time_naive)
        if to_time:
            to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
            query = query.where(OddsSnapshot.captured_at <= to_time_naive)

        # Order chronologically for charts
        query = query.order_by(OddsSnapshot.captured_at)

    result = await db.execute(query)
    rows = result.all()

    # Build history points
    history = []
    market_name = None
    result_line = None

    for row in rows:
        snapshot = row[0]  # OddsSnapshot or CompetitorOddsSnapshot
        market = row[1]  # MarketOdds or CompetitorMarketOdds

        # Capture market metadata from first row
        if market_name is None:
            market_name = market.betpawa_market_name
            result_line = market.line

        # Parse outcomes from JSONB
        outcomes = []
        if isinstance(market.outcomes, list):
            for outcome in market.outcomes:
                if isinstance(outcome, dict) and "name" in outcome and "odds" in outcome:
                    outcomes.append(
                        OutcomeOdds(name=outcome["name"], odds=outcome["odds"])
                    )

        # Calculate margin
        margin = _calculate_margin_from_outcomes(market.outcomes if isinstance(market.outcomes, list) else [])

        # Extract availability info using getattr for safe access
        unavailable_at = getattr(market, 'unavailable_at', None)
        available = unavailable_at is None

        history.append(
            OddsHistoryPoint(
                captured_at=snapshot.captured_at,
                outcomes=outcomes,
                margin=margin,
                available=available,
                unavailable_at=unavailable_at,
            )
        )

    logger.debug(
        "odds_history_query",
        event_id=event_id,
        market_id=market_id,
        bookmaker_slug=bookmaker_slug,
        is_competitor=is_competitor,
        points=len(history),
    )

    return OddsHistoryResponse(
        event_id=event_id,
        bookmaker_slug=bookmaker.slug,
        bookmaker_name=bookmaker.name,
        market_id=market_id,
        market_name=market_name or market_id,
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
    # Check if this is a competitor bookmaker
    is_competitor = bookmaker_slug in ("sportybet", "bet9ja")

    # Get bookmaker info for response
    bookmaker_result = await db.execute(
        select(Bookmaker).where(Bookmaker.slug == bookmaker_slug)
    )
    bookmaker = bookmaker_result.scalar_one_or_none()
    if not bookmaker:
        raise HTTPException(status_code=404, detail=f"Bookmaker not found: {bookmaker_slug}")

    if is_competitor:
        # Query competitor tables
        query = (
            select(CompetitorOddsSnapshot, CompetitorMarketOdds)
            .join(CompetitorEvent, CompetitorOddsSnapshot.competitor_event_id == CompetitorEvent.id)
            .join(CompetitorMarketOdds, CompetitorMarketOdds.snapshot_id == CompetitorOddsSnapshot.id)
            .where(CompetitorEvent.betpawa_event_id == event_id)
            .where(CompetitorEvent.source == bookmaker_slug)
            .where(CompetitorMarketOdds.betpawa_market_id == market_id)
        )

        # Apply line filter for specifier markets
        if line is not None:
            query = query.where(CompetitorMarketOdds.line == line)

        # Apply time filters (DB stores naive UTC)
        if from_time:
            from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
            query = query.where(CompetitorOddsSnapshot.captured_at >= from_time_naive)
        if to_time:
            to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
            query = query.where(CompetitorOddsSnapshot.captured_at <= to_time_naive)

        # Order chronologically for charts
        query = query.order_by(CompetitorOddsSnapshot.captured_at)
    else:
        # Query BetPawa tables (original behavior)
        query = (
            select(OddsSnapshot, MarketOdds)
            .join(MarketOdds, MarketOdds.snapshot_id == OddsSnapshot.id)
            .where(OddsSnapshot.event_id == event_id)
            .where(OddsSnapshot.bookmaker_id == bookmaker.id)
            .where(MarketOdds.betpawa_market_id == market_id)
        )

        # Apply line filter for specifier markets
        if line is not None:
            query = query.where(MarketOdds.line == line)

        # Apply time filters (DB stores naive UTC)
        if from_time:
            from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
            query = query.where(OddsSnapshot.captured_at >= from_time_naive)
        if to_time:
            to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
            query = query.where(OddsSnapshot.captured_at <= to_time_naive)

        # Order chronologically for charts
        query = query.order_by(OddsSnapshot.captured_at)

    result = await db.execute(query)
    rows = result.all()

    # Build history points (margin only)
    history = []
    market_name = None
    result_line = None

    for row in rows:
        snapshot = row[0]  # OddsSnapshot or CompetitorOddsSnapshot
        market = row[1]  # MarketOdds or CompetitorMarketOdds

        # Capture market metadata from first row
        if market_name is None:
            market_name = market.betpawa_market_name
            result_line = market.line

        # Calculate margin
        margin = _calculate_margin_from_outcomes(market.outcomes if isinstance(market.outcomes, list) else [])

        # Extract availability info using getattr for safe access
        unavailable_at = getattr(market, 'unavailable_at', None)
        available = unavailable_at is None

        history.append(
            MarginHistoryPoint(
                captured_at=snapshot.captured_at,
                margin=margin,
                available=available,
                unavailable_at=unavailable_at,
            )
        )

    logger.debug(
        "margin_history_query",
        event_id=event_id,
        market_id=market_id,
        bookmaker_slug=bookmaker_slug,
        is_competitor=is_competitor,
        points=len(history),
    )

    return MarginHistoryResponse(
        event_id=event_id,
        bookmaker_slug=bookmaker.slug,
        bookmaker_name=bookmaker.name,
        market_id=market_id,
        market_name=market_name or market_id,
        line=result_line,
        history=history,
    )
