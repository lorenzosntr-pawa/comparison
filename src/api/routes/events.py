"""Events API endpoints for querying matched and unmatched events."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.engine import get_db
from src.db.models.bookmaker import Bookmaker
from src.db.models.event import Event, EventBookmaker
from src.db.models.sport import Tournament
from src.matching.schemas import (
    BookmakerOdds,
    MatchedEvent,
    MatchedEventList,
    UnmatchedEvent,
)

router = APIRouter(prefix="/events", tags=["events"])


def _build_matched_event(event: Event) -> MatchedEvent:
    """Map SQLAlchemy Event to Pydantic MatchedEvent.

    Args:
        event: Event model with loaded relationships.

    Returns:
        Pydantic MatchedEvent schema.
    """
    bookmakers = [
        BookmakerOdds(
            bookmaker_slug=link.bookmaker.slug,
            bookmaker_name=link.bookmaker.name,
            external_event_id=link.external_event_id,
            event_url=link.event_url,
            has_odds=False,  # Placeholder for future odds data
        )
        for link in event.bookmaker_links
    ]

    return MatchedEvent(
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


@router.get("/{event_id}", response_model=MatchedEvent)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> MatchedEvent:
    """Get a single event by ID with all bookmaker links."""
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

    return _build_matched_event(event)


@router.get("", response_model=MatchedEventList)
async def list_events(
    db: AsyncSession = Depends(get_db),
    tournament_id: int | None = Query(default=None, description="Filter by tournament"),
    sport_id: int | None = Query(default=None, description="Filter by sport"),
    kickoff_from: datetime | None = Query(
        default=None, description="Filter events after this time"
    ),
    kickoff_to: datetime | None = Query(
        default=None, description="Filter events before this time"
    ),
    min_bookmakers: int = Query(
        default=1, ge=1, le=3, description="Minimum platforms with event"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> MatchedEventList:
    """List matched events with filtering and pagination.

    Supports filtering by tournament, sport, kickoff time range,
    and minimum number of bookmakers with the event.
    """
    # Build base query
    query = select(Event).options(
        selectinload(Event.bookmaker_links).selectinload(EventBookmaker.bookmaker),
        selectinload(Event.tournament).selectinload(Tournament.sport),
    )

    # Count query (same filters, no eager loading)
    count_query = select(func.count()).select_from(Event)

    # Apply tournament filter
    if tournament_id is not None:
        query = query.where(Event.tournament_id == tournament_id)
        count_query = count_query.where(Event.tournament_id == tournament_id)

    # Apply sport filter (join through tournament)
    if sport_id is not None:
        query = query.join(Event.tournament).where(Tournament.sport_id == sport_id)
        count_query = count_query.join(Event.tournament).where(
            Tournament.sport_id == sport_id
        )

    # Apply kickoff time filters
    if kickoff_from is not None:
        query = query.where(Event.kickoff >= kickoff_from)
        count_query = count_query.where(Event.kickoff >= kickoff_from)

    if kickoff_to is not None:
        query = query.where(Event.kickoff <= kickoff_to)
        count_query = count_query.where(Event.kickoff <= kickoff_to)

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

    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.order_by(Event.kickoff).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    events = result.scalars().unique().all()

    # Build response
    matched_events = [_build_matched_event(event) for event in events]

    return MatchedEventList(
        events=matched_events,
        total=total,
        page=page,
        page_size=page_size,
    )
