"""Palimpsest comparison API endpoints for cross-platform coverage analysis."""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.schemas.palimpsest import (
    CoverageStats,
    PalimpsestEvent,
    PalimpsestEventsResponse,
    PlatformCoverage,
    TournamentCoverage,
    TournamentGroup,
)
from src.db.engine import get_db
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorSource,
    CompetitorTournament,
)
from src.db.models.event import Event
from src.db.models.sport import Tournament

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

    # Competitor-only count: unique SR IDs with no BetPawa match (not raw rows)
    competitor_only_query = (
        select(func.count(distinct(CompetitorEvent.sportradar_id)))
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


# Type alias for availability filter values
AvailabilityFilter = Literal["all", "matched", "betpawa-only", "competitor-only"]


@router.get("/events", response_model=PalimpsestEventsResponse)
async def get_palimpsest_events(
    db: AsyncSession = Depends(get_db),
    availability: AvailabilityFilter = Query(
        default="all",
        description="Filter by availability: all | matched | betpawa-only | competitor-only",
    ),
    platforms: list[str] | None = Query(
        default=None,
        description="Filter to specific competitor platforms (sportybet, bet9ja)",
    ),
    sport_id: int | None = Query(
        default=None,
        description="Filter by sport ID",
    ),
    include_started: bool = Query(
        default=False,
        description="Include events that have already kicked off",
    ),
    search: str | None = Query(
        default=None,
        description="Search across team names and tournament names",
    ),
    sort: Literal["kickoff", "alphabetical", "tournament"] = Query(
        default="kickoff",
        description="Sort order: kickoff | alphabetical | tournament",
    ),
) -> PalimpsestEventsResponse:
    """Get palimpsest events with filtering, search, and grouping.

    Returns events grouped by tournament with coverage statistics.
    Supports filtering by availability (matched, betpawa-only, competitor-only),
    platform, sport, and full-text search.
    """
    # Time filter
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Validate platforms filter
    valid_platforms = {"sportybet", "bet9ja"}
    if platforms:
        platforms = [p.lower() for p in platforms]
        invalid = set(platforms) - valid_platforms
        if invalid:
            # Just ignore invalid platforms
            platforms = [p for p in platforms if p in valid_platforms]
            if not platforms:
                platforms = None

    # Build result lists for each category
    matched_events: list[PalimpsestEvent] = []
    betpawa_only_events: list[PalimpsestEvent] = []
    competitor_only_events: list[PalimpsestEvent] = []

    # --- Query BetPawa events with their competitor matches ---
    if availability in ("all", "matched", "betpawa-only"):
        # Get BetPawa events with tournament info
        betpawa_query = (
            select(Event)
            .options(
                selectinload(Event.tournament).selectinload(Tournament.sport),
            )
        )

        if not include_started:
            betpawa_query = betpawa_query.where(Event.kickoff > now)

        if sport_id is not None:
            betpawa_query = betpawa_query.join(Event.tournament).where(
                Tournament.sport_id == sport_id
            )

        if search:
            search_pattern = f"%{search}%"
            betpawa_query = betpawa_query.where(
                or_(
                    Event.home_team.ilike(search_pattern),
                    Event.away_team.ilike(search_pattern),
                    Event.tournament.has(Tournament.name.ilike(search_pattern)),
                )
            )

        betpawa_result = await db.execute(betpawa_query)
        betpawa_events = betpawa_result.scalars().unique().all()

        # Get competitor events that match BetPawa events (by betpawa_event_id)
        # Build a map: betpawa_event_id -> set of platforms
        betpawa_ids = [e.id for e in betpawa_events]

        # Query competitor events that have betpawa_event_id in our list
        if betpawa_ids:
            competitor_matched_query = (
                select(CompetitorEvent.betpawa_event_id, CompetitorEvent.source)
                .where(CompetitorEvent.betpawa_event_id.in_(betpawa_ids))
            )
            if platforms:
                competitor_matched_query = competitor_matched_query.where(
                    CompetitorEvent.source.in_(platforms)
                )
            competitor_matched_result = await db.execute(competitor_matched_query)
            competitor_matches = competitor_matched_result.all()

            # Build map: betpawa_event_id -> set of competitor platforms
            competitor_platforms_map: dict[int, set[str]] = {}
            for row in competitor_matches:
                if row.betpawa_event_id not in competitor_platforms_map:
                    competitor_platforms_map[row.betpawa_event_id] = set()
                competitor_platforms_map[row.betpawa_event_id].add(row.source)

            # Classify BetPawa events
            for event in betpawa_events:
                competitor_platforms = competitor_platforms_map.get(event.id, set())

                if competitor_platforms:
                    # Matched event
                    if availability in ("all", "matched"):
                        platforms_list = ["betpawa"] + sorted(competitor_platforms)
                        matched_events.append(
                            PalimpsestEvent(
                                id=event.id,
                                sportradar_id=event.sportradar_id,
                                name=event.name,
                                home_team=event.home_team,
                                away_team=event.away_team,
                                kickoff=event.kickoff,
                                tournament_name=event.tournament.name,
                                tournament_country=event.tournament.country,
                                sport_name=event.tournament.sport.name,
                                availability="matched",
                                platforms=platforms_list,
                            )
                        )
                else:
                    # BetPawa-only event
                    if availability in ("all", "betpawa-only"):
                        betpawa_only_events.append(
                            PalimpsestEvent(
                                id=event.id,
                                sportradar_id=event.sportradar_id,
                                name=event.name,
                                home_team=event.home_team,
                                away_team=event.away_team,
                                kickoff=event.kickoff,
                                tournament_name=event.tournament.name,
                                tournament_country=event.tournament.country,
                                sport_name=event.tournament.sport.name,
                                availability="betpawa-only",
                                platforms=["betpawa"],
                            )
                        )
        else:
            # No BetPawa events, nothing to classify
            pass

    # --- Query competitor-only events ---
    if availability in ("all", "competitor-only"):
        competitor_only_query = (
            select(CompetitorEvent)
            .where(CompetitorEvent.betpawa_event_id.is_(None))
            .options(
                selectinload(CompetitorEvent.tournament).selectinload(
                    CompetitorTournament.sport
                ),
            )
        )

        if not include_started:
            competitor_only_query = competitor_only_query.where(
                CompetitorEvent.kickoff > now
            )

        if platforms:
            competitor_only_query = competitor_only_query.where(
                CompetitorEvent.source.in_(platforms)
            )

        if sport_id is not None:
            competitor_only_query = competitor_only_query.join(
                CompetitorEvent.tournament
            ).where(CompetitorTournament.sport_id == sport_id)

        if search:
            search_pattern = f"%{search}%"
            competitor_only_query = competitor_only_query.where(
                or_(
                    CompetitorEvent.home_team.ilike(search_pattern),
                    CompetitorEvent.away_team.ilike(search_pattern),
                    CompetitorEvent.tournament.has(
                        CompetitorTournament.name.ilike(search_pattern)
                    ),
                )
            )

        competitor_only_result = await db.execute(competitor_only_query)
        competitor_only_rows = competitor_only_result.scalars().unique().all()

        # Group competitor-only events by SR ID to handle duplicates across platforms
        # Apply metadata priority: sportybet > bet9ja
        sr_id_events: dict[str, list[CompetitorEvent]] = {}
        for ce in competitor_only_rows:
            if ce.sportradar_id not in sr_id_events:
                sr_id_events[ce.sportradar_id] = []
            sr_id_events[ce.sportradar_id].append(ce)

        for sr_id, events_list in sr_id_events.items():
            # Sort by priority: sportybet first
            events_list.sort(
                key=lambda e: 0 if e.source == CompetitorSource.SPORTYBET else 1
            )
            # Use first (highest priority) for metadata
            primary = events_list[0]
            platforms_list = sorted(set(e.source for e in events_list))

            competitor_only_events.append(
                PalimpsestEvent(
                    id=primary.id,
                    sportradar_id=primary.sportradar_id,
                    name=primary.name,
                    home_team=primary.home_team,
                    away_team=primary.away_team,
                    kickoff=primary.kickoff,
                    tournament_name=primary.tournament.name,
                    tournament_country=primary.tournament.country_raw,
                    sport_name=primary.tournament.sport.name,
                    availability="competitor-only",
                    platforms=platforms_list,
                )
            )

    # --- Combine all events ---
    all_events = matched_events + betpawa_only_events + competitor_only_events

    # --- Apply sorting ---
    # Normalize kickoff times for comparison (strip timezone for consistent sorting)
    def get_kickoff_naive(e: PalimpsestEvent) -> datetime:
        """Get kickoff as naive datetime for sorting."""
        if e.kickoff.tzinfo is not None:
            return e.kickoff.replace(tzinfo=None)
        return e.kickoff

    if sort == "kickoff":
        all_events.sort(key=get_kickoff_naive)
    elif sort == "alphabetical":
        all_events.sort(key=lambda e: (e.home_team.lower(), e.away_team.lower()))
    elif sort == "tournament":
        all_events.sort(key=lambda e: (e.tournament_name.lower(), get_kickoff_naive(e)))

    # --- Group by tournament ---
    tournament_map: dict[str, list[PalimpsestEvent]] = {}
    for event in all_events:
        key = f"{event.tournament_name}|{event.sport_name}"
        if key not in tournament_map:
            tournament_map[key] = []
        tournament_map[key].append(event)

    # Build TournamentGroup objects
    tournament_groups: list[TournamentGroup] = []
    tournament_id_counter = 1  # Synthetic ID for grouping

    for key, events in tournament_map.items():
        # Calculate per-tournament coverage
        matched_count = sum(1 for e in events if e.availability == "matched")
        betpawa_only_count = sum(1 for e in events if e.availability == "betpawa-only")
        competitor_only_count = sum(
            1 for e in events if e.availability == "competitor-only"
        )

        # Get tournament metadata from first event
        first = events[0]

        tournament_groups.append(
            TournamentGroup(
                tournament_id=tournament_id_counter,
                tournament_name=first.tournament_name,
                tournament_country=first.tournament_country,
                sport_name=first.sport_name,
                coverage=TournamentCoverage(
                    total=len(events),
                    matched=matched_count,
                    betpawa_only=betpawa_only_count,
                    competitor_only=competitor_only_count,
                ),
                events=events,
            )
        )
        tournament_id_counter += 1

    # Sort tournament groups by name
    tournament_groups.sort(key=lambda g: g.tournament_name.lower())

    # --- Calculate overall coverage stats ---
    total_events = len(all_events)
    total_matched = sum(1 for e in all_events if e.availability == "matched")
    total_betpawa_only = sum(1 for e in all_events if e.availability == "betpawa-only")
    total_competitor_only = sum(
        1 for e in all_events if e.availability == "competitor-only"
    )
    match_rate = (total_matched / total_events * 100) if total_events > 0 else 0.0

    # Per-platform breakdown (simplified - based on filtered results)
    platform_counts: dict[str, dict[str, int]] = {
        "sportybet": {"total": 0, "matched": 0},
        "bet9ja": {"total": 0, "matched": 0},
    }
    for event in all_events:
        for platform in event.platforms:
            if platform in platform_counts:
                platform_counts[platform]["total"] += 1
                if event.availability == "matched":
                    platform_counts[platform]["matched"] += 1

    platform_stats = []
    for platform, counts in platform_counts.items():
        total = counts["total"]
        matched = counts["matched"]
        platform_stats.append(
            PlatformCoverage(
                platform=platform,
                total_events=total,
                matched_events=matched,
                unmatched_events=total - matched,
                match_rate=round((matched / total * 100) if total > 0 else 0.0, 2),
            )
        )

    coverage = CoverageStats(
        total_events=total_events,
        matched_count=total_matched,
        betpawa_only_count=total_betpawa_only,
        competitor_only_count=total_competitor_only,
        match_rate=round(match_rate, 2),
        by_platform=platform_stats,
    )

    return PalimpsestEventsResponse(
        coverage=coverage,
        tournaments=tournament_groups,
    )
