"""Palimpsest comparison API endpoints for cross-platform coverage analysis."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.palimpsest import CoverageStats, PlatformCoverage
from src.db.engine import get_db
from src.db.models.competitor import CompetitorEvent, CompetitorSource
from src.db.models.event import Event

router = APIRouter(prefix="/palimpsest", tags=["palimpsest"])


@router.get("/coverage", response_model=CoverageStats)
async def get_coverage_stats(
    db: AsyncSession = Depends(get_db),
    include_started: bool = Query(
        default=False,
        description="Include events that have already kicked off",
    ),
) -> CoverageStats:
    """Get coverage statistics across all platforms.

    Returns overall coverage summary and per-platform breakdown showing:
    - Total unique events across platforms
    - Events matched between BetPawa and competitors
    - BetPawa-only events (not on competitors)
    - Competitor-only events (not on BetPawa)
    """
    # Time filter for upcoming events
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # DB stores naive UTC

    # --- BetPawa events ---
    betpawa_query = select(func.count()).select_from(Event)
    if not include_started:
        betpawa_query = betpawa_query.where(Event.kickoff > now)
    betpawa_result = await db.execute(betpawa_query)
    total_betpawa_events = betpawa_result.scalar() or 0

    # Get all BetPawa SR IDs for later comparison
    betpawa_sr_query = select(Event.sportradar_id)
    if not include_started:
        betpawa_sr_query = betpawa_sr_query.where(Event.kickoff > now)
    betpawa_sr_result = await db.execute(betpawa_sr_query)
    betpawa_sr_ids = set(row[0] for row in betpawa_sr_result.all())

    # --- Competitor events by source ---
    platform_stats: list[PlatformCoverage] = []

    for source in [CompetitorSource.SPORTYBET, CompetitorSource.BET9JA]:
        # Total competitor events for this source
        total_query = (
            select(func.count())
            .select_from(CompetitorEvent)
            .where(CompetitorEvent.source == source.value)
        )
        if not include_started:
            total_query = total_query.where(CompetitorEvent.kickoff > now)
        total_result = await db.execute(total_query)
        total_events = total_result.scalar() or 0

        # Matched events (betpawa_event_id IS NOT NULL)
        matched_query = (
            select(func.count())
            .select_from(CompetitorEvent)
            .where(
                CompetitorEvent.source == source.value,
                CompetitorEvent.betpawa_event_id.isnot(None),
            )
        )
        if not include_started:
            matched_query = matched_query.where(CompetitorEvent.kickoff > now)
        matched_result = await db.execute(matched_query)
        matched_events = matched_result.scalar() or 0

        unmatched_events = total_events - matched_events
        match_rate = (matched_events / total_events * 100) if total_events > 0 else 0.0

        platform_stats.append(
            PlatformCoverage(
                platform=source.value,
                total_events=total_events,
                matched_events=matched_events,
                unmatched_events=unmatched_events,
                match_rate=round(match_rate, 2),
            )
        )

    # --- Calculate overall coverage stats ---

    # Matched count: distinct BetPawa events that have at least one competitor match
    matched_betpawa_query = (
        select(func.count(distinct(CompetitorEvent.betpawa_event_id)))
        .where(CompetitorEvent.betpawa_event_id.isnot(None))
    )
    if not include_started:
        matched_betpawa_query = matched_betpawa_query.where(CompetitorEvent.kickoff > now)
    matched_betpawa_result = await db.execute(matched_betpawa_query)
    matched_count = matched_betpawa_result.scalar() or 0

    # Competitor-only count: competitor events with no BetPawa match
    competitor_only_query = (
        select(func.count())
        .select_from(CompetitorEvent)
        .where(CompetitorEvent.betpawa_event_id.is_(None))
    )
    if not include_started:
        competitor_only_query = competitor_only_query.where(CompetitorEvent.kickoff > now)
    competitor_only_result = await db.execute(competitor_only_query)
    competitor_only_count = competitor_only_result.scalar() or 0

    # BetPawa-only count: BetPawa events with SR ID not in any competitor event
    # Get competitor SR IDs
    competitor_sr_query = select(distinct(CompetitorEvent.sportradar_id))
    if not include_started:
        competitor_sr_query = competitor_sr_query.where(CompetitorEvent.kickoff > now)
    competitor_sr_result = await db.execute(competitor_sr_query)
    competitor_sr_ids = set(row[0] for row in competitor_sr_result.all())

    # Count BetPawa events whose SR ID is not in competitor SR IDs
    betpawa_only_count = len(betpawa_sr_ids - competitor_sr_ids)

    # Total unique events = matched + betpawa_only + competitor_only
    total_events = matched_count + betpawa_only_count + competitor_only_count

    # Overall match rate
    match_rate = (matched_count / total_events * 100) if total_events > 0 else 0.0

    return CoverageStats(
        total_events=total_events,
        matched_count=matched_count,
        betpawa_only_count=betpawa_only_count,
        competitor_only_count=competitor_only_count,
        match_rate=round(match_rate, 2),
        by_platform=platform_stats,
    )
