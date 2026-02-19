"""Events API endpoints for querying matched and unmatched events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.caching.odds_cache import OddsCache
from src.db.engine import get_db
from src.db.models.bookmaker import Bookmaker
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
    CompetitorSource,
    CompetitorTournament,
)
from src.db.models.event import Event, EventBookmaker
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.db.models.sport import Tournament
from src.matching.schemas import (
    BookmakerMarketData,
    BookmakerOdds,
    EventDetailResponse,
    InlineOdds,
    MarketOddsDetail,
    MatchedEvent,
    MatchedEventList,
    OutcomeDetail,
    OutcomeOdds,
    TournamentSummary,
    UnmatchedEvent,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/events", tags=["events"])

# Key market IDs for inline odds (Betpawa taxonomy)
# 3743 = 1X2 Full Time, 5000 = Over/Under Full Time, 3795 = Both Teams To Score Full Time, 4693 = Double Chance Full Time
INLINE_MARKET_IDS = ["3743", "5000", "3795", "4693"]

# Market names to exclude from detail view (goalscorer markets - not focus for now)
EXCLUDED_MARKET_PATTERNS = ["goalscorer", "scorer"]


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def get_odds_cache(request: Request) -> OddsCache | None:
    """Get OddsCache from app state, or None if not initialized."""
    return getattr(request.app.state, "odds_cache", None)


async def _load_snapshots_cached(
    event_ids: list[int],
    cache: OddsCache | None,
    db: AsyncSession,
) -> tuple[dict[int, dict[int, Any]], dict[int, dict[str, Any]]]:
    """Load snapshots from cache first, falling back to DB for misses.

    Returns:
        Tuple of (betpawa_snapshots_by_event, competitor_snapshots_by_event)
    """
    if cache is None:
        # No cache available -- full DB path
        betpawa = await _load_latest_snapshots_for_events(db, event_ids)
        competitor = await _load_competitor_snapshots_for_events(db, event_ids)
        logger.debug(
            "snapshot_loading",
            total_requested=len(event_ids),
            cache_hits=0,
            cache_misses=len(event_ids),
            source="db_only",
        )
        return betpawa, competitor

    # Try cache first
    betpawa = cache.get_betpawa_snapshots(event_ids)
    competitor = cache.get_competitor_snapshots(event_ids)

    # Check for cache misses INDEPENDENTLY for betpawa and competitor
    # An event might have competitor data cached but not betpawa (or vice versa)
    # We must check each cache separately to ensure complete data
    cached_bp_ids = set(betpawa.keys())
    cached_comp_ids = set(competitor.keys())

    # Betpawa cache misses - fetch from DB
    bp_miss_ids = [eid for eid in event_ids if eid not in cached_bp_ids]
    if bp_miss_ids:
        db_betpawa = await _load_latest_snapshots_for_events(db, bp_miss_ids)
        betpawa.update(db_betpawa)

    # Competitor cache misses - fetch from DB
    comp_miss_ids = [eid for eid in event_ids if eid not in cached_comp_ids]
    if comp_miss_ids:
        db_competitor = await _load_competitor_snapshots_for_events(db, comp_miss_ids)
        competitor.update(db_competitor)

    logger.debug(
        "snapshot_loading",
        total_requested=len(event_ids),
        bp_cache_hits=len(cached_bp_ids),
        bp_cache_misses=len(bp_miss_ids),
        comp_cache_hits=len(cached_comp_ids),
        comp_cache_misses=len(comp_miss_ids),
        source="cache" if not bp_miss_ids and not comp_miss_ids else "mixed",
    )

    return betpawa, competitor


def _get_snapshot_time(snapshot) -> datetime | None:
    """Get freshness timestamp preferring last_confirmed_at over captured_at.

    last_confirmed_at represents when the odds were last verified (updated every
    scrape cycle), while captured_at represents when the odds last changed.
    For freshness display, we want the verification time.
    """
    if not snapshot:
        return None
    return getattr(snapshot, "last_confirmed_at", None) or snapshot.captured_at


def _build_inline_odds(snapshot: OddsSnapshot | None) -> list[InlineOdds]:
    """Extract inline odds for key markets from a snapshot.

    Args:
        snapshot: OddsSnapshot with loaded markets, or None.

    Returns:
        List of InlineOdds for key markets (1X2, O/U 2.5, BTTS).
    """
    if not snapshot or not snapshot.markets:
        return []

    inline_odds = []
    for market in snapshot.markets:
        if market.betpawa_market_id in INLINE_MARKET_IDS:
            # For Over/Under (5000), only include line=2.5
            if market.betpawa_market_id == "5000" and market.line != 2.5:
                continue

            # Parse outcomes from JSONB
            outcomes = []
            if isinstance(market.outcomes, list):
                for outcome in market.outcomes:
                    if isinstance(outcome, dict) and "name" in outcome and "odds" in outcome:
                        outcomes.append(
                            OutcomeOdds(name=outcome["name"], odds=outcome["odds"])
                        )

            # Calculate margin if outcomes exist
            margin = None
            if outcomes:
                try:
                    total_implied_prob = sum(1.0 / o.odds for o in outcomes if o.odds > 0)
                    if total_implied_prob > 0:
                        margin = round((total_implied_prob - 1) * 100, 2)
                except (ZeroDivisionError, TypeError):
                    pass

            # Extract availability from market (CachedMarket or MarketOdds)
            unavailable_at = getattr(market, "unavailable_at", None)
            available = unavailable_at is None

            # Always append market (even if outcomes empty/margin null)
            # This ensures consistency with event detail endpoint
            inline_odds.append(
                InlineOdds(
                    market_id=market.betpawa_market_id,
                    market_name=market.betpawa_market_name,
                    line=market.line,
                    outcomes=outcomes,
                    margin=margin,
                    available=available,
                    unavailable_since=unavailable_at,
                )
            )

    return inline_odds


def _build_matched_event(
    event: Event,
    snapshots_by_bookmaker: dict[int, OddsSnapshot] | None = None,
    competitor_snapshots: dict[str, CompetitorOddsSnapshot] | None = None,
) -> MatchedEvent:
    """Map SQLAlchemy Event to Pydantic MatchedEvent.

    Args:
        event: Event model with loaded relationships.
        snapshots_by_bookmaker: Optional dict mapping bookmaker_id to latest OddsSnapshot.
        competitor_snapshots: Optional dict mapping source ('sportybet'/'bet9ja') to CompetitorOddsSnapshot.

    Returns:
        Pydantic MatchedEvent schema.
    """
    snapshots_by_bookmaker = snapshots_by_bookmaker or {}
    competitor_snapshots = competitor_snapshots or {}

    bookmakers = []
    for link in event.bookmaker_links:
        # Check if this is a competitor bookmaker
        if link.bookmaker.slug in ("sportybet", "bet9ja"):
            # Use competitor snapshot
            comp_snapshot = competitor_snapshots.get(link.bookmaker.slug)
            inline_odds = _build_competitor_inline_odds(comp_snapshot)
            has_odds = bool(comp_snapshot and comp_snapshot.markets)
            snapshot_time = _get_snapshot_time(comp_snapshot)
        else:
            # BetPawa - use regular snapshot
            snapshot = snapshots_by_bookmaker.get(link.bookmaker_id)
            inline_odds = _build_inline_odds(snapshot)
            has_odds = bool(snapshot and snapshot.markets)
            snapshot_time = _get_snapshot_time(snapshot)

        bookmakers.append(
            BookmakerOdds(
                bookmaker_slug=link.bookmaker.slug,
                bookmaker_name=link.bookmaker.name,
                external_event_id=link.external_event_id,
                event_url=link.event_url,
                has_odds=has_odds,
                inline_odds=inline_odds,
                snapshot_time=snapshot_time,
            )
        )

    return MatchedEvent(
        id=event.id,
        sportradar_id=event.sportradar_id,
        name=event.name,
        home_team=event.home_team,
        away_team=event.away_team,
        kickoff=event.kickoff,
        tournament_id=event.tournament_id,
        tournament_name=event.tournament.name,
        tournament_country=event.tournament.country,
        sport_name=event.tournament.sport.name,
        bookmakers=bookmakers,
        created_at=event.created_at,
    )


async def _load_latest_snapshots_for_events(
    db: AsyncSession,
    event_ids: list[int],
) -> dict[int, dict[int, OddsSnapshot]]:
    """Load the latest OddsSnapshot per bookmaker for multiple events.

    Uses a subquery to get only the latest snapshot per (event_id, bookmaker_id) pair,
    then eagerly loads markets for inline odds.

    Args:
        db: Async database session.
        event_ids: List of event IDs to load snapshots for.

    Returns:
        Dict mapping event_id -> {bookmaker_id: OddsSnapshot}.
    """
    if not event_ids:
        return {}

    # Subquery to find the latest snapshot ID per (event_id, bookmaker_id)
    latest_subq = (
        select(
            OddsSnapshot.event_id,
            OddsSnapshot.bookmaker_id,
            func.max(OddsSnapshot.id).label("max_id"),
        )
        .where(OddsSnapshot.event_id.in_(event_ids))
        .group_by(OddsSnapshot.event_id, OddsSnapshot.bookmaker_id)
        .subquery()
    )

    # Main query: fetch snapshots matching the latest IDs, with markets eagerly loaded
    query = (
        select(OddsSnapshot)
        .join(
            latest_subq,
            (OddsSnapshot.event_id == latest_subq.c.event_id)
            & (OddsSnapshot.bookmaker_id == latest_subq.c.bookmaker_id)
            & (OddsSnapshot.id == latest_subq.c.max_id),
        )
        .options(selectinload(OddsSnapshot.markets))
    )

    result = await db.execute(query)
    snapshots = result.scalars().all()

    # Build nested dict: event_id -> bookmaker_id -> snapshot
    snapshots_by_event: dict[int, dict[int, OddsSnapshot]] = {}
    for snapshot in snapshots:
        if snapshot.event_id not in snapshots_by_event:
            snapshots_by_event[snapshot.event_id] = {}
        snapshots_by_event[snapshot.event_id][snapshot.bookmaker_id] = snapshot

    return snapshots_by_event


async def _load_competitor_snapshots_for_events(
    db: AsyncSession,
    event_ids: list[int],
) -> dict[int, dict[str, CompetitorOddsSnapshot]]:
    """Load latest CompetitorOddsSnapshot for events that have competitor matches.

    Args:
        db: Async database session.
        event_ids: List of BetPawa event IDs.

    Returns:
        Dict mapping event_id -> {source: CompetitorOddsSnapshot}
        where source is 'sportybet' or 'bet9ja'
    """
    if not event_ids:
        return {}

    # Find CompetitorEvents linked to these BetPawa events
    comp_events_query = select(CompetitorEvent).where(
        CompetitorEvent.betpawa_event_id.in_(event_ids)
    )
    comp_events_result = await db.execute(comp_events_query)
    comp_events = comp_events_result.scalars().all()

    if not comp_events:
        return {}

    comp_event_ids = [ce.id for ce in comp_events]

    # Subquery to find latest snapshot per competitor_event_id
    latest_subq = (
        select(
            CompetitorOddsSnapshot.competitor_event_id,
            func.max(CompetitorOddsSnapshot.id).label("max_id"),
        )
        .where(CompetitorOddsSnapshot.competitor_event_id.in_(comp_event_ids))
        .group_by(CompetitorOddsSnapshot.competitor_event_id)
        .subquery()
    )

    # Load snapshots with markets
    snapshots_query = (
        select(CompetitorOddsSnapshot)
        .join(
            latest_subq,
            (CompetitorOddsSnapshot.competitor_event_id == latest_subq.c.competitor_event_id)
            & (CompetitorOddsSnapshot.id == latest_subq.c.max_id),
        )
        .options(selectinload(CompetitorOddsSnapshot.markets))
    )

    snapshots_result = await db.execute(snapshots_query)
    snapshots = snapshots_result.scalars().all()

    # Build mapping: comp_event_id -> snapshot
    snapshot_by_comp_event = {s.competitor_event_id: s for s in snapshots}

    # Build final mapping: betpawa_event_id -> source -> snapshot
    result: dict[int, dict[str, CompetitorOddsSnapshot]] = {}
    for ce in comp_events:
        snapshot = snapshot_by_comp_event.get(ce.id)
        if snapshot:
            if ce.betpawa_event_id not in result:
                result[ce.betpawa_event_id] = {}
            result[ce.betpawa_event_id][ce.source] = snapshot

    return result


def _build_competitor_inline_odds(
    snapshot: CompetitorOddsSnapshot | None,
) -> list[InlineOdds]:
    """Extract inline odds for key markets from a competitor snapshot.

    Args:
        snapshot: CompetitorOddsSnapshot with loaded markets, or None.

    Returns:
        List of InlineOdds for key markets (1X2, O/U 2.5, BTTS).
    """
    if not snapshot or not snapshot.markets:
        return []

    inline_odds = []
    for market in snapshot.markets:
        if market.betpawa_market_id in INLINE_MARKET_IDS:
            # For Over/Under (5000), only include line=2.5
            if market.betpawa_market_id == "5000" and market.line != 2.5:
                continue

            # Parse outcomes from JSONB
            outcomes = []
            if isinstance(market.outcomes, list):
                for outcome in market.outcomes:
                    if isinstance(outcome, dict) and "name" in outcome and "odds" in outcome:
                        outcomes.append(
                            OutcomeOdds(name=outcome["name"], odds=outcome["odds"])
                        )

            # Calculate margin if outcomes exist
            margin = None
            if outcomes:
                try:
                    total_implied_prob = sum(1.0 / o.odds for o in outcomes if o.odds > 0)
                    if total_implied_prob > 0:
                        margin = round((total_implied_prob - 1) * 100, 2)
                except (ZeroDivisionError, TypeError):
                    pass

            # Extract availability from market (CachedMarket or CompetitorMarketOdds)
            unavailable_at = getattr(market, "unavailable_at", None)
            available = unavailable_at is None

            # Always append market (even if outcomes empty/margin null)
            # This ensures consistency with event detail endpoint
            inline_odds.append(
                InlineOdds(
                    market_id=market.betpawa_market_id,
                    market_name=market.betpawa_market_name,
                    line=market.line,
                    outcomes=outcomes,
                    margin=margin,
                    available=available,
                    unavailable_since=unavailable_at,
                )
            )

    return inline_odds


async def _load_latest_competitor_snapshots(
    db: AsyncSession,
    competitor_event_ids: list[int],
) -> dict[int, CompetitorOddsSnapshot]:
    """Load the latest CompetitorOddsSnapshot per competitor event.

    Args:
        db: Async database session.
        competitor_event_ids: List of competitor event IDs to load snapshots for.

    Returns:
        Dict mapping competitor_event_id -> CompetitorOddsSnapshot.
    """
    if not competitor_event_ids:
        return {}

    # Subquery to find the latest snapshot ID per competitor_event_id
    latest_subq = (
        select(
            CompetitorOddsSnapshot.competitor_event_id,
            func.max(CompetitorOddsSnapshot.id).label("max_id"),
        )
        .where(CompetitorOddsSnapshot.competitor_event_id.in_(competitor_event_ids))
        .group_by(CompetitorOddsSnapshot.competitor_event_id)
        .subquery()
    )

    # Main query: fetch snapshots matching the latest IDs, with markets eagerly loaded
    query = (
        select(CompetitorOddsSnapshot)
        .join(
            latest_subq,
            (CompetitorOddsSnapshot.competitor_event_id == latest_subq.c.competitor_event_id)
            & (CompetitorOddsSnapshot.id == latest_subq.c.max_id),
        )
        .options(selectinload(CompetitorOddsSnapshot.markets))
    )

    result = await db.execute(query)
    snapshots = result.scalars().all()

    # Build dict: competitor_event_id -> snapshot
    return {snapshot.competitor_event_id: snapshot for snapshot in snapshots}


def _build_competitor_event_response(
    primary_event: CompetitorEvent,
    all_events_by_sr: list[CompetitorEvent],
    snapshots_by_event: dict[int, CompetitorOddsSnapshot],
) -> MatchedEvent:
    """Build a MatchedEvent response for competitor-only events.

    Uses negative ID to distinguish from BetPawa events.
    Applies metadata priority: sportybet > bet9ja.

    Args:
        primary_event: The primary competitor event (for metadata).
        all_events_by_sr: All competitor events with the same SR ID.
        snapshots_by_event: Dict mapping competitor_event_id to snapshot.

    Returns:
        MatchedEvent with negative ID and competitor odds.
    """
    # Build bookmakers list - one entry per competitor platform
    bookmakers = []
    for ce in all_events_by_sr:
        snapshot = snapshots_by_event.get(ce.id)
        inline_odds = _build_competitor_inline_odds(snapshot)

        # Map source to bookmaker_slug
        bookmaker_slug = ce.source  # sportybet or bet9ja
        bookmaker_name = "SportyBet" if ce.source == CompetitorSource.SPORTYBET else "Bet9ja"

        bookmakers.append(
            BookmakerOdds(
                bookmaker_slug=bookmaker_slug,
                bookmaker_name=bookmaker_name,
                external_event_id=ce.external_id,
                event_url=None,  # Competitor events don't have URLs stored
                has_odds=bool(snapshot and snapshot.markets),
                inline_odds=inline_odds,
                snapshot_time=_get_snapshot_time(snapshot),
            )
        )

    # Use negative ID for competitor-only events
    return MatchedEvent(
        id=-primary_event.id,  # Negative ID to distinguish from BetPawa events
        sportradar_id=primary_event.sportradar_id,
        name=primary_event.name,
        home_team=primary_event.home_team,
        away_team=primary_event.away_team,
        kickoff=primary_event.kickoff,
        tournament_id=primary_event.tournament_id,
        tournament_name=primary_event.tournament.name,
        tournament_country=primary_event.tournament.country_raw,
        sport_name=primary_event.tournament.sport.name,
        bookmakers=bookmakers,
        created_at=primary_event.created_at,
    )


def _calculate_margin(outcomes: list[OutcomeDetail]) -> float | None:
    """Calculate margin (overround) for a market.

    Margin = (sum(1/odds) - 1) * 100

    Args:
        outcomes: List of outcomes with odds values.

    Returns:
        Margin as a percentage, or None if calculation not possible.
    """
    if not outcomes:
        return None

    try:
        total_implied_prob = sum(1.0 / o.odds for o in outcomes if o.odds > 0)
        if total_implied_prob == 0:
            return None
        margin = (total_implied_prob - 1) * 100
        return round(margin, 2)
    except (ZeroDivisionError, TypeError):
        return None


def _build_market_detail(market: MarketOdds) -> MarketOddsDetail:
    """Build detailed market odds from a MarketOdds model.

    Args:
        market: MarketOdds model with outcomes.

    Returns:
        MarketOddsDetail with calculated margin.
    """
    outcomes = []
    if isinstance(market.outcomes, list):
        for outcome in market.outcomes:
            if isinstance(outcome, dict) and "name" in outcome and "odds" in outcome:
                outcomes.append(
                    OutcomeDetail(
                        name=outcome["name"],
                        odds=outcome["odds"],
                        is_active=outcome.get("is_active", True),
                    )
                )

    margin = _calculate_margin(outcomes)

    # Extract availability from market (MarketOdds ORM model)
    unavailable_at = getattr(market, "unavailable_at", None)
    available = unavailable_at is None

    return MarketOddsDetail(
        betpawa_market_id=market.betpawa_market_id,
        betpawa_market_name=market.betpawa_market_name,
        line=market.line,
        outcomes=outcomes,
        margin=margin,
        market_groups=market.market_groups,
        available=available,
        unavailable_since=unavailable_at,
    )


def _is_excluded_market(market_name: str) -> bool:
    """Check if a market should be excluded from detail view.

    Args:
        market_name: The market name to check.

    Returns:
        True if market should be excluded, False otherwise.
    """
    name_lower = market_name.lower()
    return any(pattern in name_lower for pattern in EXCLUDED_MARKET_PATTERNS)


def _build_bookmaker_market_data(
    link: EventBookmaker,
    snapshot: OddsSnapshot | None,
) -> BookmakerMarketData:
    """Build complete market data for a single bookmaker.

    Excludes goalscorer markets and other excluded market types.

    Args:
        link: EventBookmaker with bookmaker relationship loaded.
        snapshot: Latest OddsSnapshot for this bookmaker, or None.

    Returns:
        BookmakerMarketData with all markets (excluding goalscorer markets).
    """
    markets = []
    snapshot_time = _get_snapshot_time(snapshot)

    if snapshot:
        for market in snapshot.markets:
            # Skip excluded markets (goalscorer, etc.)
            if _is_excluded_market(market.betpawa_market_name):
                continue
            markets.append(_build_market_detail(market))

    return BookmakerMarketData(
        bookmaker_slug=link.bookmaker.slug,
        bookmaker_name=link.bookmaker.name,
        snapshot_time=snapshot_time,
        markets=markets,
    )


def _build_competitor_market_detail(market: CompetitorMarketOdds) -> MarketOddsDetail:
    """Build detailed market odds from a CompetitorMarketOdds model.

    Args:
        market: CompetitorMarketOdds model with outcomes.

    Returns:
        MarketOddsDetail with calculated margin.
    """
    outcomes = []
    if isinstance(market.outcomes, list):
        for outcome in market.outcomes:
            if isinstance(outcome, dict) and "name" in outcome and "odds" in outcome:
                outcomes.append(
                    OutcomeDetail(
                        name=outcome["name"],
                        odds=outcome["odds"],
                        is_active=outcome.get("is_active", True),
                    )
                )

    margin = _calculate_margin(outcomes)

    # Extract availability from market (CompetitorMarketOdds ORM model)
    unavailable_at = getattr(market, "unavailable_at", None)
    available = unavailable_at is None

    return MarketOddsDetail(
        betpawa_market_id=market.betpawa_market_id,
        betpawa_market_name=market.betpawa_market_name,
        line=market.line,
        outcomes=outcomes,
        margin=margin,
        market_groups=market.market_groups,
        available=available,
        unavailable_since=unavailable_at,
    )


def _build_competitor_bookmaker_market_data(
    bookmaker_slug: str,
    bookmaker_name: str,
    snapshot: CompetitorOddsSnapshot | None,
) -> BookmakerMarketData:
    """Build complete market data for a competitor bookmaker.

    Args:
        bookmaker_slug: The bookmaker slug (sportybet, bet9ja).
        bookmaker_name: The bookmaker display name.
        snapshot: Latest CompetitorOddsSnapshot for this bookmaker, or None.

    Returns:
        BookmakerMarketData with all markets (excluding goalscorer markets).
    """
    markets = []
    snapshot_time = _get_snapshot_time(snapshot)

    if snapshot:
        for market in snapshot.markets:
            # Skip excluded markets (goalscorer, etc.)
            if _is_excluded_market(market.betpawa_market_name):
                continue
            markets.append(_build_competitor_market_detail(market))

    return BookmakerMarketData(
        bookmaker_slug=bookmaker_slug,
        bookmaker_name=bookmaker_name,
        snapshot_time=snapshot_time,
        markets=markets,
    )


def _build_event_detail_response(
    event: Event,
    snapshots_by_bookmaker: dict[int, OddsSnapshot] | None = None,
    competitor_snapshots: dict[str, CompetitorOddsSnapshot] | None = None,
) -> EventDetailResponse:
    """Build full event detail response with all market data.

    Args:
        event: Event model with loaded relationships.
        snapshots_by_bookmaker: Dict mapping bookmaker_id to latest OddsSnapshot.
        competitor_snapshots: Dict mapping source ('sportybet'/'bet9ja') to CompetitorOddsSnapshot.

    Returns:
        EventDetailResponse with inline odds and full market data.
    """
    snapshots_by_bookmaker = snapshots_by_bookmaker or {}
    competitor_snapshots = competitor_snapshots or {}

    # Build basic bookmaker info with inline odds
    bookmakers = []
    markets_by_bookmaker = []

    for link in event.bookmaker_links:
        # Check if this is a competitor bookmaker
        if link.bookmaker.slug in ("sportybet", "bet9ja"):
            # Use competitor snapshot
            comp_snapshot = competitor_snapshots.get(link.bookmaker.slug)
            inline_odds = _build_competitor_inline_odds(comp_snapshot)
            has_odds = bool(comp_snapshot and comp_snapshot.markets)

            bookmakers.append(
                BookmakerOdds(
                    bookmaker_slug=link.bookmaker.slug,
                    bookmaker_name=link.bookmaker.name,
                    external_event_id=link.external_event_id,
                    event_url=link.event_url,
                    has_odds=has_odds,
                    inline_odds=inline_odds,
                    snapshot_time=_get_snapshot_time(comp_snapshot),
                )
            )

            # Build full market data for this competitor bookmaker
            markets_by_bookmaker.append(
                _build_competitor_bookmaker_market_data(
                    link.bookmaker.slug,
                    link.bookmaker.name,
                    comp_snapshot,
                )
            )
        else:
            # BetPawa - use regular snapshot
            snapshot = snapshots_by_bookmaker.get(link.bookmaker_id)
            inline_odds = _build_inline_odds(snapshot)

            bookmakers.append(
                BookmakerOdds(
                    bookmaker_slug=link.bookmaker.slug,
                    bookmaker_name=link.bookmaker.name,
                    external_event_id=link.external_event_id,
                    event_url=link.event_url,
                    has_odds=bool(snapshot and snapshot.markets),
                    inline_odds=inline_odds,
                    snapshot_time=_get_snapshot_time(snapshot),
                )
            )

            # Build full market data for this bookmaker
            markets_by_bookmaker.append(
                _build_bookmaker_market_data(link, snapshot)
            )

    return EventDetailResponse(
        id=event.id,
        sportradar_id=event.sportradar_id,
        name=event.name,
        home_team=event.home_team,
        away_team=event.away_team,
        kickoff=event.kickoff,
        tournament_id=event.tournament_id,
        tournament_name=event.tournament.name,
        sport_name=event.tournament.sport.name,
        bookmakers=bookmakers,
        created_at=event.created_at,
        markets_by_bookmaker=markets_by_bookmaker,
    )


@router.get("/unmatched", response_model=list[UnmatchedEvent])
async def list_unmatched_events(
    db: AsyncSession = Depends(get_db),
    missing_platform: str | None = Query(
        default=None,
        description="Show events missing from this platform (e.g., 'betpawa')",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> list[UnmatchedEvent]:
    """List events with partial platform coverage.

    Returns events that are not present on all three platforms.
    Useful for monitoring data quality and matching issues.
    """
    # Get all bookmaker slugs for comparison
    bookmakers_result = await db.execute(select(Bookmaker.id, Bookmaker.slug))
    bookmaker_map = {row.id: row.slug for row in bookmakers_result}
    all_platform_slugs = set(bookmaker_map.values())

    # Build query for events with fewer than 3 bookmaker links
    # Subquery to count bookmaker links per event
    bookmaker_count_subq = (
        select(
            EventBookmaker.event_id,
            func.count(EventBookmaker.bookmaker_id).label("bookmaker_count"),
        )
        .group_by(EventBookmaker.event_id)
        .subquery()
    )

    # Base query for events with partial coverage
    query = (
        select(Event)
        .join(bookmaker_count_subq, Event.id == bookmaker_count_subq.c.event_id)
        .where(bookmaker_count_subq.c.bookmaker_count < len(all_platform_slugs))
        .options(
            selectinload(Event.bookmaker_links).selectinload(EventBookmaker.bookmaker)
        )
    )

    # If filtering by missing platform
    if missing_platform:
        # Get bookmaker ID for the platform
        bookmaker_result = await db.execute(
            select(Bookmaker.id).where(Bookmaker.slug == missing_platform)
        )
        bookmaker_row = bookmaker_result.scalar_one_or_none()

        if bookmaker_row is None:
            raise HTTPException(
                status_code=400, detail=f"Unknown platform: {missing_platform}"
            )

        # Find events NOT linked to this bookmaker
        events_with_platform = select(EventBookmaker.event_id).where(
            EventBookmaker.bookmaker_id == bookmaker_row
        )
        query = query.where(Event.id.notin_(events_with_platform))

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    events = result.scalars().unique().all()

    # Build response with missing_on info
    unmatched_events = []
    for event in events:
        present_slugs = {link.bookmaker.slug for link in event.bookmaker_links}
        missing_slugs = list(all_platform_slugs - present_slugs)

        # Determine which platform has it (first one found)
        platform = present_slugs.pop() if present_slugs else "unknown"

        unmatched_events.append(
            UnmatchedEvent(
                id=event.id,
                sportradar_id=event.sportradar_id,
                name=event.name,
                kickoff=event.kickoff,
                platform=platform,
                missing_on=missing_slugs,
            )
        )

    return unmatched_events


@router.get("/countries", response_model=list[str])
async def list_countries(
    db: AsyncSession = Depends(get_db),
    availability: Literal["betpawa", "competitor"] | None = Query(
        default=None,
        description="Filter countries by availability: betpawa (countries with BetPawa events) | competitor (countries with competitor-only events)",
    ),
) -> list[str]:
    """List all countries for filter dropdowns.

    Returns unique countries sorted alphabetically, optionally filtered by
    availability mode.

    When availability='competitor', returns only countries that have upcoming
    competitor-only events (events on SportyBet/Bet9ja but not BetPawa).
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if availability == "competitor":
        # Countries with competitor-only events (CompetitorEvent where betpawa_event_id IS NULL)
        query = (
            select(CompetitorTournament.country_raw)
            .distinct()
            .join(CompetitorEvent, CompetitorTournament.id == CompetitorEvent.tournament_id)
            .where(
                CompetitorEvent.betpawa_event_id.is_(None),
                CompetitorEvent.kickoff > now,
                CompetitorTournament.country_raw.isnot(None),
            )
            .order_by(CompetitorTournament.country_raw)
        )
    else:
        # Countries with BetPawa events (default or availability='betpawa')
        query = (
            select(Tournament.country)
            .distinct()
            .join(Event, Tournament.id == Event.tournament_id)
            .where(
                Event.kickoff > now,
                Tournament.country.isnot(None),
            )
            .order_by(Tournament.country)
        )

    result = await db.execute(query)
    countries = [row[0] for row in result.all()]

    return countries


@router.get("/tournaments", response_model=list[TournamentSummary])
async def list_tournaments(
    db: AsyncSession = Depends(get_db),
    with_events_only: bool = Query(
        default=True, description="Only return tournaments that have events"
    ),
    availability: Literal["betpawa", "competitor"] | None = Query(
        default=None,
        description="Filter tournaments by availability: betpawa (tournaments with BetPawa events) | competitor (tournaments with competitor-only events)",
    ),
) -> list[TournamentSummary]:
    """List all tournaments for filter dropdowns.

    Returns tournaments sorted by name, optionally filtered to only
    those that have events in the database.

    When availability='competitor', returns BetPawa tournaments that have
    matching competitor-only events (matched by tournament name).
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if availability == "competitor":
        # For competitor mode, find BetPawa tournaments that have competitor-only events
        # (CompetitorEvent where betpawa_event_id IS NULL, matched by tournament name)
        # First get competitor tournament names with upcoming competitor-only events
        comp_tournament_names_query = (
            select(func.lower(CompetitorTournament.name))
            .distinct()
            .join(CompetitorEvent, CompetitorTournament.id == CompetitorEvent.tournament_id)
            .where(
                CompetitorEvent.betpawa_event_id.is_(None),
                CompetitorEvent.kickoff > now,
            )
        )

        # Return BetPawa tournaments that match these names (case-insensitive)
        query = (
            select(Tournament)
            .where(func.lower(Tournament.name).in_(comp_tournament_names_query))
            .order_by(Tournament.name)
        )
    elif with_events_only:
        # Only tournaments that have at least one upcoming BetPawa event
        query = (
            select(Tournament)
            .where(
                Tournament.id.in_(
                    select(Event.tournament_id)
                    .where(Event.kickoff > now)
                    .distinct()
                )
            )
            .order_by(Tournament.name)
        )
    else:
        query = select(Tournament).order_by(Tournament.name)

    result = await db.execute(query)
    tournaments = result.scalars().all()

    return [
        TournamentSummary(
            id=t.id,
            name=t.name,
            country=t.country,
        )
        for t in tournaments
    ]


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EventDetailResponse:
    """Get a single event by ID with full market odds for comparison.

    Returns all bookmaker links with:
    - Inline odds for key markets (1X2, O/U 2.5, BTTS)
    - Full market data with all outcomes and margin calculations
    """
    result = await db.execute(
        select(Event)
        .where(Event.id == event_id)
        .options(
            selectinload(Event.bookmaker_links).selectinload(EventBookmaker.bookmaker),
            selectinload(Event.tournament).selectinload(Tournament.sport),
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Load snapshots via cache-first strategy
    cache = get_odds_cache(request)
    snapshots_by_event, competitor_snapshots_by_event = await _load_snapshots_cached(
        [event.id], cache, db
    )

    return _build_event_detail_response(
        event,
        snapshots_by_event.get(event.id),
        competitor_snapshots_by_event.get(event.id),
    )


@router.get("/alerts/count")
async def get_alerts_count(
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """Get count of events with availability issues.

    Returns the number of upcoming BetPawa events that have at least one
    market with unavailable_at set in the LATEST snapshot (either BetPawa
    or competitor markets).
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Subquery to get latest BetPawa snapshot ID per event
    latest_bp_snapshot_subq = (
        select(
            OddsSnapshot.event_id,
            func.max(OddsSnapshot.id).label("max_id"),
        )
        .group_by(OddsSnapshot.event_id)
        .subquery()
    )

    # Find event IDs with unavailable BetPawa markets in LATEST snapshot only
    bp_events_with_alerts = (
        select(OddsSnapshot.event_id)
        .join(
            latest_bp_snapshot_subq,
            (OddsSnapshot.event_id == latest_bp_snapshot_subq.c.event_id)
            & (OddsSnapshot.id == latest_bp_snapshot_subq.c.max_id),
        )
        .join(MarketOdds, MarketOdds.snapshot_id == OddsSnapshot.id)
        .join(Event, Event.id == OddsSnapshot.event_id)
        .where(
            MarketOdds.unavailable_at.isnot(None),
            Event.kickoff > now,
        )
        .distinct()
    )

    # Subquery to get latest competitor snapshot ID per competitor_event
    latest_comp_snapshot_subq = (
        select(
            CompetitorOddsSnapshot.competitor_event_id,
            func.max(CompetitorOddsSnapshot.id).label("max_id"),
        )
        .group_by(CompetitorOddsSnapshot.competitor_event_id)
        .subquery()
    )

    # Find event IDs with unavailable competitor markets in LATEST snapshot only
    comp_events_with_alerts = (
        select(CompetitorEvent.betpawa_event_id)
        .join(
            CompetitorOddsSnapshot,
            CompetitorOddsSnapshot.competitor_event_id == CompetitorEvent.id,
        )
        .join(
            latest_comp_snapshot_subq,
            (CompetitorOddsSnapshot.competitor_event_id == latest_comp_snapshot_subq.c.competitor_event_id)
            & (CompetitorOddsSnapshot.id == latest_comp_snapshot_subq.c.max_id),
        )
        .join(
            CompetitorMarketOdds,
            CompetitorMarketOdds.snapshot_id == CompetitorOddsSnapshot.id,
        )
        .join(Event, Event.id == CompetitorEvent.betpawa_event_id)
        .where(
            CompetitorMarketOdds.unavailable_at.isnot(None),
            CompetitorEvent.betpawa_event_id.isnot(None),
            Event.kickoff > now,
        )
        .distinct()
    )

    # Union both queries and count distinct event IDs
    union_query = bp_events_with_alerts.union(comp_events_with_alerts).subquery()
    count_query = select(func.count()).select_from(union_query)

    result = await db.execute(count_query)
    count = result.scalar() or 0

    return {"count": count}


@router.get("", response_model=MatchedEventList)
async def list_events(
    request: Request,
    db: AsyncSession = Depends(get_db),
    availability: Literal["betpawa", "competitor", "alerts"] = Query(
        default="betpawa",
        description="Filter by availability: betpawa (only BetPawa events) | competitor (competitor-only events) | alerts (events with unavailable markets)",
    ),
    tournament_id: int | None = Query(default=None, description="Filter by single tournament (deprecated, use tournament_ids)"),
    tournament_ids: list[int] | None = Query(default=None, description="Filter by multiple tournament IDs"),
    sport_id: int | None = Query(default=None, description="Filter by sport"),
    kickoff_from: datetime | None = Query(
        default=None, description="Filter events after this time"
    ),
    kickoff_to: datetime | None = Query(
        default=None, description="Filter events before this time"
    ),
    include_started: bool = Query(
        default=False, description="Include events that have already started"
    ),
    min_bookmakers: int = Query(
        default=1, ge=1, le=3, description="Minimum platforms with event"
    ),
    search: str | None = Query(
        default=None, description="Search by team name (home or away)"
    ),
    countries: list[str] | None = Query(
        default=None, description="Filter by country/region names (case-insensitive)"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> MatchedEventList:
    """List matched events with filtering and pagination.

    Supports filtering by tournament, sport, kickoff time range,
    and minimum number of bookmakers with the event.

    By default, only upcoming events are shown (kickoff > now).
    Set include_started=true to also show events that have already started.

    When availability='all', includes competitor-only events (events that exist
    on SportyBet/Bet9ja but not on BetPawa). These events have negative IDs
    and use metadata priority: sportybet > bet9ja.
    """
    # Common time filter
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # DB stores naive UTC
    kickoff_from_naive = None
    kickoff_to_naive = None
    if kickoff_from is not None:
        kickoff_from_naive = kickoff_from.replace(tzinfo=None) if kickoff_from.tzinfo else kickoff_from
    if kickoff_to is not None:
        kickoff_to_naive = kickoff_to.replace(tzinfo=None) if kickoff_to.tzinfo else kickoff_to

    # ---- BetPawa Events Query ----
    query = select(Event).options(
        selectinload(Event.bookmaker_links).selectinload(EventBookmaker.bookmaker),
        selectinload(Event.tournament).selectinload(Tournament.sport),
    )
    count_query = select(func.count()).select_from(Event)

    # By default, only show upcoming events (kickoff > now)
    if not include_started:
        query = query.where(Event.kickoff > now)
        count_query = count_query.where(Event.kickoff > now)

    # Apply tournament filter (support both single and multiple IDs)
    if tournament_ids:
        query = query.where(Event.tournament_id.in_(tournament_ids))
        count_query = count_query.where(Event.tournament_id.in_(tournament_ids))
    elif tournament_id is not None:
        query = query.where(Event.tournament_id == tournament_id)
        count_query = count_query.where(Event.tournament_id == tournament_id)

    # Track if we've already joined tournament (to avoid duplicate joins)
    tournament_joined = False

    # Apply sport filter (join through tournament)
    if sport_id is not None:
        query = query.join(Event.tournament).where(Tournament.sport_id == sport_id)
        count_query = count_query.join(Event.tournament).where(
            Tournament.sport_id == sport_id
        )
        tournament_joined = True

    # Apply country filter (join through tournament if not already joined)
    if countries:
        if not tournament_joined:
            query = query.join(Event.tournament)
            count_query = count_query.join(Event.tournament)
            tournament_joined = True
        # Case-insensitive country matching
        country_conditions = [
            func.lower(Tournament.country) == country.lower()
            for country in countries
        ]
        query = query.where(or_(*country_conditions))
        count_query = count_query.where(or_(*country_conditions))

    # Apply kickoff time filters
    if kickoff_from_naive is not None:
        query = query.where(Event.kickoff >= kickoff_from_naive)
        count_query = count_query.where(Event.kickoff >= kickoff_from_naive)
    if kickoff_to_naive is not None:
        query = query.where(Event.kickoff <= kickoff_to_naive)
        count_query = count_query.where(Event.kickoff <= kickoff_to_naive)

    # Apply team name search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Event.home_team.ilike(search_pattern))
            | (Event.away_team.ilike(search_pattern))
        )
        count_query = count_query.where(
            (Event.home_team.ilike(search_pattern))
            | (Event.away_team.ilike(search_pattern))
        )

    # Apply min_bookmakers filter using subquery
    if min_bookmakers > 1:
        bookmaker_count_subq = (
            select(
                EventBookmaker.event_id,
                func.count(EventBookmaker.bookmaker_id).label("bookmaker_count"),
            )
            .group_by(EventBookmaker.event_id)
            .having(func.count(EventBookmaker.bookmaker_id) >= min_bookmakers)
            .subquery()
        )
        query = query.join(
            bookmaker_count_subq, Event.id == bookmaker_count_subq.c.event_id
        )
        count_query = count_query.join(
            bookmaker_count_subq, Event.id == bookmaker_count_subq.c.event_id
        )

    # ---- Competitor-Only Events (when availability='competitor') ----
    competitor_events_response: list[MatchedEvent] = []
    competitor_count = 0

    if availability == "competitor":
        # Query competitor events where betpawa_event_id IS NULL
        comp_query = (
            select(CompetitorEvent)
            .where(CompetitorEvent.betpawa_event_id.is_(None))
            .options(
                selectinload(CompetitorEvent.tournament).selectinload(
                    CompetitorTournament.sport
                ),
            )
        )
        comp_count_query = (
            select(func.count())
            .select_from(CompetitorEvent)
            .where(CompetitorEvent.betpawa_event_id.is_(None))
        )

        # Apply time filters
        if not include_started:
            comp_query = comp_query.where(CompetitorEvent.kickoff > now)
            comp_count_query = comp_count_query.where(CompetitorEvent.kickoff > now)
        if kickoff_from_naive is not None:
            comp_query = comp_query.where(CompetitorEvent.kickoff >= kickoff_from_naive)
            comp_count_query = comp_count_query.where(
                CompetitorEvent.kickoff >= kickoff_from_naive
            )
        if kickoff_to_naive is not None:
            comp_query = comp_query.where(CompetitorEvent.kickoff <= kickoff_to_naive)
            comp_count_query = comp_count_query.where(
                CompetitorEvent.kickoff <= kickoff_to_naive
            )

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            comp_query = comp_query.where(
                or_(
                    CompetitorEvent.home_team.ilike(search_pattern),
                    CompetitorEvent.away_team.ilike(search_pattern),
                )
            )
            comp_count_query = comp_count_query.where(
                or_(
                    CompetitorEvent.home_team.ilike(search_pattern),
                    CompetitorEvent.away_team.ilike(search_pattern),
                )
            )

        # Track if we've joined competitor tournament
        comp_tournament_joined = False

        # Apply sport filter (join through competitor tournament)
        if sport_id is not None:
            comp_query = comp_query.join(CompetitorEvent.tournament).where(
                CompetitorTournament.sport_id == sport_id
            )
            comp_count_query = comp_count_query.join(CompetitorEvent.tournament).where(
                CompetitorTournament.sport_id == sport_id
            )
            comp_tournament_joined = True

        # Apply country filter for competitor events
        if countries:
            if not comp_tournament_joined:
                comp_query = comp_query.join(CompetitorEvent.tournament)
                comp_count_query = comp_count_query.join(CompetitorEvent.tournament)
                comp_tournament_joined = True
            # Case-insensitive country matching (CompetitorTournament uses country_raw, not country)
            country_conditions = [
                func.lower(CompetitorTournament.country_raw) == country.lower()
                for country in countries
            ]
            comp_query = comp_query.where(or_(*country_conditions))
            comp_count_query = comp_count_query.where(or_(*country_conditions))

        # Tournament filter for competitor events via tournament name + country matching
        if tournament_ids:
            # Get tournament names and countries from BetPawa Tournament table
            tournament_info_query = select(Tournament.name, Tournament.country).where(
                Tournament.id.in_(tournament_ids)
            )
            tournament_info_result = await db.execute(tournament_info_query)
            tournament_info = [(row[0], row[1]) for row in tournament_info_result.all()]

            if tournament_info:
                # Filter CompetitorEvents where tournament name AND country match
                # Need to join tournament if not already joined
                if not comp_tournament_joined:
                    comp_query = comp_query.join(CompetitorEvent.tournament)
                    comp_count_query = comp_count_query.join(CompetitorEvent.tournament)

                # Build conditions matching name (case-insensitive) and country
                # Handle null countries by matching NULL in CompetitorTournament.country_raw
                name_country_conditions = []
                for name, country in tournament_info:
                    if country is None:
                        # Match tournaments with NULL country
                        condition = and_(
                            func.lower(CompetitorTournament.name) == name.lower(),
                            CompetitorTournament.country_raw.is_(None),
                        )
                    else:
                        # Match tournaments with specific country (case-insensitive)
                        condition = and_(
                            func.lower(CompetitorTournament.name) == name.lower(),
                            func.lower(CompetitorTournament.country_raw) == country.lower(),
                        )
                    name_country_conditions.append(condition)

                comp_query = comp_query.where(or_(*name_country_conditions))
                comp_count_query = comp_count_query.where(or_(*name_country_conditions))
            else:
                # tournament_ids provided but no matching BetPawa tournaments found
                # Return empty result (no competitor events match non-existent tournaments)
                return MatchedEventList(
                    events=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                )

        # Get all competitor-only events (we need to dedupe by SR ID and apply metadata priority)
        comp_result = await db.execute(comp_query)
        comp_events = comp_result.scalars().unique().all()

        # Group by sportradar_id and apply metadata priority
        sr_id_events: dict[str, list[CompetitorEvent]] = {}
        for ce in comp_events:
            if ce.sportradar_id not in sr_id_events:
                sr_id_events[ce.sportradar_id] = []
            sr_id_events[ce.sportradar_id].append(ce)

        # Load odds for all competitor events
        all_comp_event_ids = [ce.id for ce in comp_events]
        comp_snapshots = await _load_latest_competitor_snapshots(db, all_comp_event_ids)

        # Build response for each unique SR ID (deduplicated)
        deduped_events: list[tuple[CompetitorEvent, list[CompetitorEvent]]] = []
        for sr_id, events_list in sr_id_events.items():
            # Sort by priority: sportybet first
            events_list.sort(
                key=lambda e: 0 if e.source == CompetitorSource.SPORTYBET else 1
            )
            primary = events_list[0]
            deduped_events.append((primary, events_list))

        # Count unique competitor events (after deduplication)
        competitor_count = len(deduped_events)

        # Build response objects
        for primary, all_events in deduped_events:
            competitor_events_response.append(
                _build_competitor_event_response(primary, all_events, comp_snapshots)
            )

    # For availability='competitor', return only competitor events
    if availability == "competitor":
        # Sort competitor events by kickoff
        competitor_events_response.sort(
            key=lambda e: e.kickoff.replace(tzinfo=None) if e.kickoff.tzinfo else e.kickoff
        )

        # Apply pagination
        offset = (page - 1) * page_size
        paginated_events = competitor_events_response[offset : offset + page_size]

        return MatchedEventList(
            events=paginated_events,
            total=competitor_count,
            page=page,
            page_size=page_size,
        )

    # ---- Alerts Events (when availability='alerts') ----
    if availability == "alerts":
        # Subquery to get latest BetPawa snapshot ID per event
        latest_bp_snapshot_subq = (
            select(
                OddsSnapshot.event_id,
                func.max(OddsSnapshot.id).label("max_id"),
            )
            .group_by(OddsSnapshot.event_id)
            .subquery()
        )

        # Find event IDs with unavailable BetPawa markets in LATEST snapshot only
        bp_events_with_alerts = (
            select(OddsSnapshot.event_id)
            .join(
                latest_bp_snapshot_subq,
                (OddsSnapshot.event_id == latest_bp_snapshot_subq.c.event_id)
                & (OddsSnapshot.id == latest_bp_snapshot_subq.c.max_id),
            )
            .join(MarketOdds, MarketOdds.snapshot_id == OddsSnapshot.id)
            .join(Event, Event.id == OddsSnapshot.event_id)
            .where(
                MarketOdds.unavailable_at.isnot(None),
                Event.kickoff > now,
            )
            .distinct()
        )

        # Subquery to get latest competitor snapshot ID per competitor_event
        latest_comp_snapshot_subq = (
            select(
                CompetitorOddsSnapshot.competitor_event_id,
                func.max(CompetitorOddsSnapshot.id).label("max_id"),
            )
            .group_by(CompetitorOddsSnapshot.competitor_event_id)
            .subquery()
        )

        # Find event IDs with unavailable competitor markets in LATEST snapshot only
        comp_events_with_alerts = (
            select(CompetitorEvent.betpawa_event_id)
            .join(
                CompetitorOddsSnapshot,
                CompetitorOddsSnapshot.competitor_event_id == CompetitorEvent.id,
            )
            .join(
                latest_comp_snapshot_subq,
                (CompetitorOddsSnapshot.competitor_event_id == latest_comp_snapshot_subq.c.competitor_event_id)
                & (CompetitorOddsSnapshot.id == latest_comp_snapshot_subq.c.max_id),
            )
            .join(
                CompetitorMarketOdds,
                CompetitorMarketOdds.snapshot_id == CompetitorOddsSnapshot.id,
            )
            .join(Event, Event.id == CompetitorEvent.betpawa_event_id)
            .where(
                CompetitorMarketOdds.unavailable_at.isnot(None),
                CompetitorEvent.betpawa_event_id.isnot(None),
                Event.kickoff > now,
            )
            .distinct()
        )

        # Union both queries to get all event IDs with alerts
        alerts_event_ids_subq = bp_events_with_alerts.union(
            comp_events_with_alerts
        ).subquery()

        # Apply alerts filter to main query
        query = query.where(Event.id.in_(select(alerts_event_ids_subq)))
        count_query = count_query.where(Event.id.in_(select(alerts_event_ids_subq)))

    # Standard flow (availability='betpawa' or 'alerts')
    # Get BetPawa event count
    count_result = await db.execute(count_query)
    betpawa_total = count_result.scalar() or 0
    offset = (page - 1) * page_size
    query = query.order_by(Event.kickoff).offset(offset).limit(page_size)

    result = await db.execute(query)
    events = result.scalars().unique().all()

    event_ids = [event.id for event in events]
    cache = get_odds_cache(request)
    snapshots_by_event, competitor_snapshots_by_event = await _load_snapshots_cached(
        event_ids, cache, db
    )

    matched_events = [
        _build_matched_event(
            event,
            snapshots_by_event.get(event.id),
            competitor_snapshots_by_event.get(event.id),
        )
        for event in events
    ]

    return MatchedEventList(
        events=matched_events,
        total=betpawa_total,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}/alerts")
async def get_event_alerts(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get risk alerts for a specific event.

    Returns all risk alerts associated with the given event,
    with counts by status for badge display.

    Args:
        event_id: ID of the event to get alerts for.
        db: Async database session (injected).

    Returns:
        RiskAlertsResponse with alerts filtered by event_id.
    """
    from src.api.schemas.alerts import RiskAlertResponse, RiskAlertsResponse
    from src.db.models.risk_alert import RiskAlert

    # Get alerts for this event
    result = await db.execute(
        select(RiskAlert)
        .where(RiskAlert.event_id == event_id)
        .order_by(desc(RiskAlert.detected_at))
    )
    alerts = result.scalars().all()

    # Count by status
    status_counts: dict[str, int] = {"new": 0, "acknowledged": 0, "past": 0}
    for alert in alerts:
        if alert.status in status_counts:
            status_counts[alert.status] += 1

    return RiskAlertsResponse(
        alerts=[RiskAlertResponse.model_validate(alert) for alert in alerts],
        total=len(alerts),
        new_count=status_counts["new"],
        acknowledged_count=status_counts["acknowledged"],
        past_count=status_counts["past"],
    )
