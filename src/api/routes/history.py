"""Historical data API endpoints for odds and margin history.

Updated in Phase 109 to use market_odds_history table instead of deprecated
snapshot-based tables (OddsSnapshot, MarketOdds, CompetitorOddsSnapshot, etc.).
"""

from __future__ import annotations

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_db
from src.db.models.bookmaker import Bookmaker
from src.db.models.market_odds import MarketOddsHistory
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

    # Query market_odds_history with unified bookmaker_slug
    query = (
        select(MarketOddsHistory)
        .where(MarketOddsHistory.event_id == event_id)
        .where(MarketOddsHistory.bookmaker_slug == bookmaker_slug)
        .where(MarketOddsHistory.betpawa_market_id == market_id)
    )

    # Apply line filter for specifier markets
    if line is not None:
        query = query.where(MarketOddsHistory.line == line)

    # Apply time filters (MarketOddsHistory uses timezone-aware timestamps)
    if from_time:
        from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
        query = query.where(MarketOddsHistory.captured_at >= from_time_naive)
    if to_time:
        to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
        query = query.where(MarketOddsHistory.captured_at <= to_time_naive)

    # Order chronologically for charts
    query = query.order_by(MarketOddsHistory.captured_at)

    result = await db.execute(query)
    rows = result.scalars().all()

    # Build history points
    history = []
    result_line = None

    for market in rows:
        # Capture line from first row
        if result_line is None:
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
        margin = _calculate_margin_from_outcomes(
            market.outcomes if isinstance(market.outcomes, list) else []
        )

        # MarketOddsHistory does NOT have unavailable_at - history only contains
        # changed records, so availability changes create separate history entries.
        # Return available=True and unavailable_at=None for all history points.
        history.append(
            OddsHistoryPoint(
                captured_at=market.captured_at,
                outcomes=outcomes,
                margin=margin,
                available=True,
                unavailable_at=None,
            )
        )

    logger.debug(
        "odds_history_query",
        event_id=event_id,
        market_id=market_id,
        bookmaker_slug=bookmaker_slug,
        points=len(history),
    )

    return OddsHistoryResponse(
        event_id=event_id,
        bookmaker_slug=bookmaker.slug,
        bookmaker_name=bookmaker.name,
        market_id=market_id,
        market_name=market_id,  # MarketOddsHistory doesn't store market_name
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

    # Query market_odds_history with unified bookmaker_slug
    query = (
        select(MarketOddsHistory)
        .where(MarketOddsHistory.event_id == event_id)
        .where(MarketOddsHistory.bookmaker_slug == bookmaker_slug)
        .where(MarketOddsHistory.betpawa_market_id == market_id)
    )

    # Apply line filter for specifier markets
    if line is not None:
        query = query.where(MarketOddsHistory.line == line)

    # Apply time filters (MarketOddsHistory uses timezone-aware timestamps)
    if from_time:
        from_time_naive = from_time.replace(tzinfo=None) if from_time.tzinfo else from_time
        query = query.where(MarketOddsHistory.captured_at >= from_time_naive)
    if to_time:
        to_time_naive = to_time.replace(tzinfo=None) if to_time.tzinfo else to_time
        query = query.where(MarketOddsHistory.captured_at <= to_time_naive)

    # Order chronologically for charts
    query = query.order_by(MarketOddsHistory.captured_at)

    result = await db.execute(query)
    rows = result.scalars().all()

    # Build history points (margin only)
    history = []
    result_line = None

    for market in rows:
        # Capture line from first row
        if result_line is None:
            result_line = market.line

        # Calculate margin
        margin = _calculate_margin_from_outcomes(
            market.outcomes if isinstance(market.outcomes, list) else []
        )

        # MarketOddsHistory does NOT have unavailable_at - history only contains
        # changed records, so availability changes create separate history entries.
        # Return available=True and unavailable_at=None for all history points.
        history.append(
            MarginHistoryPoint(
                captured_at=market.captured_at,
                margin=margin,
                available=True,
                unavailable_at=None,
            )
        )

    logger.debug(
        "margin_history_query",
        event_id=event_id,
        market_id=market_id,
        bookmaker_slug=bookmaker_slug,
        points=len(history),
    )

    return MarginHistoryResponse(
        event_id=event_id,
        bookmaker_slug=bookmaker.slug,
        bookmaker_name=bookmaker.name,
        market_id=market_id,
        market_name=market_id,  # MarketOddsHistory doesn't store market_name
        line=result_line,
        history=history,
    )
