"""Event matching service with upsert logic for cross-platform events."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.db.models.event import Event, EventBookmaker
from src.db.models.sport import Tournament
from src.scraping.schemas import Platform

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.matching.schemas import ProcessingResult


class EventMatchingService:
    """Service for matching and upserting events across platforms.

    Uses PostgreSQL INSERT...ON CONFLICT for atomic upserts.
    Implements Betpawa-first metadata priority:
    - Betpawa updates metadata (name, home_team, away_team)
    - Competitors insert-only for metadata (except kickoff which is always updated)
    """

    async def upsert_tournament(
        self,
        db: AsyncSession,
        platform: Platform,
        data: dict,
    ) -> Tournament:
        """Upsert tournament by sportradar_id.

        Args:
            db: Async database session.
            platform: Source platform for this data.
            data: Tournament data with keys:
                - sportradar_id: str | None
                - name: str
                - sport_id: int
                - country: str | None

        Returns:
            Tournament with id populated.
        """
        sportradar_id = data.get("sportradar_id")
        name = data["name"]
        sport_id = data["sport_id"]
        country = data.get("country")

        if sportradar_id:
            # Upsert by sportradar_id
            stmt = insert(Tournament).values(
                sportradar_id=sportradar_id,
                name=name,
                sport_id=sport_id,
                country=country,
            )

            if platform == Platform.BETPAWA:
                # Betpawa always updates metadata
                stmt = stmt.on_conflict_do_update(
                    index_elements=["sportradar_id"],
                    set_={
                        "name": stmt.excluded.name,
                        "country": stmt.excluded.country,
                    },
                )
            else:
                # Competitors: insert-only, don't overwrite existing metadata
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["sportradar_id"],
                )

            stmt = stmt.returning(Tournament)
            result = await db.execute(stmt)
            row = result.fetchone()

            if row:
                return row[0]

            # If on_conflict_do_nothing returned nothing, fetch existing
            existing = await db.execute(
                select(Tournament).where(
                    Tournament.sportradar_id == sportradar_id
                )
            )
            return existing.scalar_one()

        else:
            # No sportradar_id - look up by name + sport_id
            existing = await db.execute(
                select(Tournament).where(
                    Tournament.name == name,
                    Tournament.sport_id == sport_id,
                )
            )
            tournament = existing.scalar_one_or_none()

            if tournament:
                # Update if Betpawa
                if platform == Platform.BETPAWA and country:
                    tournament.country = country
                return tournament

            # Create new
            tournament = Tournament(
                name=name,
                sport_id=sport_id,
                country=country,
            )
            db.add(tournament)
            await db.flush()
            return tournament

    async def upsert_event(
        self,
        db: AsyncSession,
        platform: Platform,
        tournament_id: int,
        data: dict,
    ) -> Event:
        """Upsert event by sportradar_id.

        Args:
            db: Async database session.
            platform: Source platform for this data.
            tournament_id: ID of the parent tournament.
            data: Event data with keys:
                - sportradar_id: str
                - name: str
                - home_team: str
                - away_team: str
                - kickoff: datetime

        Returns:
            Event with id populated.
        """
        sportradar_id = data["sportradar_id"]
        name = data["name"]
        home_team = data["home_team"]
        away_team = data["away_team"]
        kickoff = data["kickoff"]

        stmt = insert(Event).values(
            sportradar_id=sportradar_id,
            tournament_id=tournament_id,
            name=name,
            home_team=home_team,
            away_team=away_team,
            kickoff=kickoff,
        )

        if platform == Platform.BETPAWA:
            # Betpawa updates all metadata
            stmt = stmt.on_conflict_do_update(
                index_elements=["sportradar_id"],
                set_={
                    "name": stmt.excluded.name,
                    "home_team": stmt.excluded.home_team,
                    "away_team": stmt.excluded.away_team,
                    "kickoff": stmt.excluded.kickoff,
                    "tournament_id": stmt.excluded.tournament_id,
                },
            )
        else:
            # Competitors: only update kickoff (time corrections)
            stmt = stmt.on_conflict_do_update(
                index_elements=["sportradar_id"],
                set_={
                    "kickoff": stmt.excluded.kickoff,
                },
            )

        stmt = stmt.returning(Event)
        result = await db.execute(stmt)
        row = result.fetchone()
        return row[0]

    async def upsert_event_bookmaker(
        self,
        db: AsyncSession,
        event_id: int,
        bookmaker_id: int,
        external_event_id: str,
        event_url: str | None = None,
    ) -> EventBookmaker:
        """Upsert event-bookmaker link.

        Args:
            db: Async database session.
            event_id: Internal event ID.
            bookmaker_id: Internal bookmaker ID.
            external_event_id: Platform-specific event ID.
            event_url: Optional URL to event on platform.

        Returns:
            EventBookmaker with id populated.
        """
        stmt = insert(EventBookmaker).values(
            event_id=event_id,
            bookmaker_id=bookmaker_id,
            external_event_id=external_event_id,
            event_url=event_url,
        )

        # Always update external_event_id and event_url (may change)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_event_bookmaker",
            set_={
                "external_event_id": stmt.excluded.external_event_id,
                "event_url": stmt.excluded.event_url,
            },
        )

        stmt = stmt.returning(EventBookmaker)
        result = await db.execute(stmt)
        row = result.fetchone()
        return row[0]

    async def get_events_by_sportradar_ids(
        self,
        db: AsyncSession,
        sportradar_ids: list[str],
    ) -> dict[str, Event]:
        """Bulk fetch events by sportradar IDs.

        Args:
            db: Async database session.
            sportradar_ids: List of sportradar IDs to fetch.

        Returns:
            Dict mapping sportradar_id to Event for O(1) lookup.
        """
        if not sportradar_ids:
            return {}

        result = await db.execute(
            select(Event).where(Event.sportradar_id.in_(sportradar_ids))
        )
        events = result.scalars().all()

        return {event.sportradar_id: event for event in events}

    async def process_scraped_events(
        self,
        db: AsyncSession,
        platform: Platform,
        bookmaker_id: int,
        events: list[dict],
    ) -> ProcessingResult:
        """Process a batch of scraped events.

        Orchestration method that upserts tournaments, events, and bookmaker links.

        Args:
            db: Async database session.
            platform: Source platform.
            bookmaker_id: Internal bookmaker ID.
            events: List of event dicts with keys:
                - sportradar_id: str
                - name: str
                - home_team: str
                - away_team: str
                - kickoff: datetime
                - external_event_id: str
                - event_url: str | None
                - tournament: dict with sportradar_id, name, sport_id, country

        Returns:
            ProcessingResult with counts.
        """
        new_events = 0
        updated_events = 0
        new_tournaments = 0

        # Collect sportradar_ids for bulk lookup
        sportradar_ids = [e["sportradar_id"] for e in events]
        existing_events = await self.get_events_by_sportradar_ids(
            db, sportradar_ids
        )

        # Track tournaments we've already processed this batch
        tournament_cache: dict[str, Tournament] = {}

        for event_data in events:
            # Handle tournament
            tournament_data = event_data["tournament"]
            tournament_key = tournament_data.get("sportradar_id") or (
                f"{tournament_data['name']}:{tournament_data['sport_id']}"
            )

            if tournament_key not in tournament_cache:
                # Check if this is a new tournament by looking it up first
                if tournament_data.get("sportradar_id"):
                    existing_tournament = await db.execute(
                        select(Tournament).where(
                            Tournament.sportradar_id
                            == tournament_data["sportradar_id"]
                        )
                    )
                    is_new_tournament = (
                        existing_tournament.scalar_one_or_none() is None
                    )
                else:
                    existing_tournament = await db.execute(
                        select(Tournament).where(
                            Tournament.name == tournament_data["name"],
                            Tournament.sport_id == tournament_data["sport_id"],
                        )
                    )
                    is_new_tournament = (
                        existing_tournament.scalar_one_or_none() is None
                    )

                tournament = await self.upsert_tournament(
                    db, platform, tournament_data
                )
                tournament_cache[tournament_key] = tournament

                if is_new_tournament:
                    new_tournaments += 1
            else:
                tournament = tournament_cache[tournament_key]

            # Check if event is new
            is_new_event = (
                event_data["sportradar_id"] not in existing_events
            )

            # Upsert event
            event = await self.upsert_event(
                db,
                platform,
                tournament.id,
                {
                    "sportradar_id": event_data["sportradar_id"],
                    "name": event_data["name"],
                    "home_team": event_data["home_team"],
                    "away_team": event_data["away_team"],
                    "kickoff": event_data["kickoff"],
                },
            )

            if is_new_event:
                new_events += 1
            else:
                updated_events += 1

            # Upsert event-bookmaker link
            await self.upsert_event_bookmaker(
                db,
                event.id,
                bookmaker_id,
                event_data["external_event_id"],
                event_data.get("event_url"),
            )

        return ProcessingResult(
            new_events=new_events,
            updated_events=updated_events,
            new_tournaments=new_tournaments,
        )
