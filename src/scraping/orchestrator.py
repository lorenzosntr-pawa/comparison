"""Scraping orchestrator for concurrent platform execution."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.db.models.bookmaker import Bookmaker
from src.db.models.event import Event
from src.db.models.odds import OddsSnapshot
from src.matching.service import EventMatchingService
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.exceptions import InvalidEventIdError
from src.scraping.schemas import Platform, PlatformResult, ScrapeResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ScrapingOrchestrator:
    """Orchestrates concurrent scraping across all platforms."""

    def __init__(
        self,
        sportybet_client: SportyBetClient,
        betpawa_client: BetPawaClient,
        bet9ja_client: Bet9jaClient,
    ) -> None:
        """Initialize with client instances.

        Args:
            sportybet_client: Async SportyBet client.
            betpawa_client: Async BetPawa client.
            bet9ja_client: Async Bet9ja client.
        """
        self._clients = {
            Platform.SPORTYBET: sportybet_client,
            Platform.BETPAWA: betpawa_client,
            Platform.BET9JA: bet9ja_client,
        }

    async def scrape_all(
        self,
        platforms: list[Platform] | None = None,
        sport_id: str | None = None,
        competition_id: str | None = None,
        include_data: bool = False,
        timeout: float = 30.0,
        scrape_run_id: int | None = None,
        db: AsyncSession | None = None,
    ) -> ScrapeResult:
        """Scrape all (or specified) platforms concurrently.

        Uses asyncio.gather(return_exceptions=True) for partial failure tolerance.
        If one platform fails, others continue and complete.

        Args:
            platforms: List of platforms to scrape (default: all).
            sport_id: Filter to specific sport (e.g., "2" for football).
            competition_id: Filter to specific competition.
            include_data: Whether to include raw event data in results.
            timeout: Per-platform timeout in seconds.
            scrape_run_id: Optional ScrapeRun ID for error logging.
            db: Optional database session for error logging.

        Returns:
            ScrapeResult with status and per-platform results.
        """
        started_at = datetime.now(timezone.utc)
        target_platforms = platforms or list(Platform)

        # Create tasks for each platform
        tasks = [
            self._scrape_platform(
                platform, sport_id, competition_id, include_data, timeout, db
            )
            for platform in target_platforms
        ]

        # Execute concurrently with return_exceptions=True
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        platform_results: list[PlatformResult] = []
        for platform, result in zip(target_platforms, results):
            if isinstance(result, Exception):
                # Platform failed - log error to database if session provided
                if db and scrape_run_id:
                    await self._log_error(db, scrape_run_id, platform, result)
                platform_results.append(
                    PlatformResult(
                        platform=platform,
                        success=False,
                        events_count=0,
                        error_message=str(result),
                        duration_ms=0,
                        events=None,
                    )
                )
            else:
                # Platform succeeded - result is (events, duration_ms)
                events, duration_ms = result

                # Store events in database if session provided
                if db and events:
                    try:
                        await self._store_events(db, platform, events)
                    except Exception as e:
                        logger.exception(
                            f"Failed to store events for {platform}: {e}"
                        )
                        if scrape_run_id:
                            await self._log_error(
                                db, scrape_run_id, platform, e
                            )

                platform_results.append(
                    PlatformResult(
                        platform=platform,
                        success=True,
                        events_count=len(events),
                        error_message=None,
                        duration_ms=duration_ms,
                        events=events if include_data else None,
                    )
                )

        # Commit all changes (logged errors + stored events)
        if db:
            await db.commit()

        completed_at = datetime.now(timezone.utc)

        # Determine overall status
        success_count = sum(1 for r in platform_results if r.success)
        if success_count == len(platform_results):
            status = "completed"
        elif success_count > 0:
            status = "partial"
        else:
            status = "failed"

        total_events = sum(r.events_count for r in platform_results if r.success)

        return ScrapeResult(
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            platforms=platform_results,
            total_events=total_events,
        )

    async def _scrape_platform(
        self,
        platform: Platform,
        sport_id: str | None,
        competition_id: str | None,
        include_data: bool,
        timeout: float,
        db: AsyncSession | None = None,
    ) -> tuple[list[dict], int]:
        """Scrape a single platform with timeout.

        Args:
            platform: Platform to scrape.
            sport_id: Filter to specific sport (e.g., "2" for football).
            competition_id: Filter to specific competition.
            include_data: Whether to return event data.
            timeout: Timeout in seconds.
            db: Optional database session (required for SportyBet/Bet9ja).

        Returns:
            Tuple of (events list, duration in ms).

        Raises:
            asyncio.TimeoutError: If operation exceeds timeout.
            Exception: Any error from the underlying client.
        """
        start_time = time.perf_counter()

        async def _do_scrape() -> list[dict]:
            client = self._clients[platform]

            if platform == Platform.BETPAWA:
                return await self._scrape_betpawa(client, competition_id)
            elif platform == Platform.SPORTYBET:
                if db is None:
                    logger.warning(
                        "SportyBet scraping requires database session - skipping"
                    )
                    return []
                return await self._scrape_sportybet(client, db)
            elif platform == Platform.BET9JA:
                if db is None:
                    logger.warning(
                        "Bet9ja scraping requires database session - skipping"
                    )
                    return []
                return await self._scrape_bet9ja(client, db)
            else:
                return []

        # Apply timeout
        events = await asyncio.wait_for(_do_scrape(), timeout=timeout)

        end_time = time.perf_counter()
        duration_ms = int((end_time - start_time) * 1000)

        return events, duration_ms

    async def _scrape_betpawa(
        self,
        client: BetPawaClient,
        competition_id: str | None = None,
    ) -> list[dict]:
        """Scrape events from BetPawa.

        Args:
            client: BetPawa API client.
            competition_id: Optional specific competition ID to scrape.

        Returns:
            List of event dicts in standard format for EventMatchingService.
        """
        events: list[dict] = []

        if competition_id:
            # Scrape specific competition
            competitions_to_scrape = [competition_id]
        else:
            # Discover all football competitions
            competitions_to_scrape = await self._get_betpawa_competitions(client)

        logger.info(
            f"Scraping {len(competitions_to_scrape)} BetPawa competitions"
        )

        for comp_id in competitions_to_scrape:
            try:
                comp_events = await self._scrape_betpawa_competition(
                    client, comp_id
                )
                events.extend(comp_events)
            except Exception as e:
                logger.warning(
                    f"Failed to scrape BetPawa competition {comp_id}: {e}"
                )
                # Continue with other competitions

        logger.info(f"Scraped {len(events)} events from BetPawa")
        return events

    async def _get_betpawa_competitions(
        self,
        client: BetPawaClient,
    ) -> list[str]:
        """Get list of competition IDs from BetPawa.

        Args:
            client: BetPawa API client.

        Returns:
            List of competition IDs to scrape.
        """
        categories_data = await client.fetch_categories("2")  # Football

        competition_ids = []
        regions = categories_data.get("regions", [])

        for region in regions:
            competitions = region.get("competitions", [])
            for comp in competitions:
                comp_data = comp.get("competition", {})
                comp_id = comp_data.get("id")
                if comp_id:
                    competition_ids.append(str(comp_id))

        return competition_ids

    async def _scrape_betpawa_competition(
        self,
        client: BetPawaClient,
        competition_id: str,
    ) -> list[dict]:
        """Scrape events from a single BetPawa competition.

        Args:
            client: BetPawa API client.
            competition_id: Competition ID to scrape.

        Returns:
            List of event dicts in standard format.
        """
        events_response = await client.fetch_events(
            competition_id=competition_id,
            state="UPCOMING",
            page=1,
            size=100,
        )

        events = []
        responses = events_response.get("responses", [])

        if not responses:
            return events

        first_response = responses[0]
        events_data = first_response.get("responses", [])

        for event_data in events_data:
            parsed = self._parse_betpawa_event(event_data)
            if parsed:
                events.append(parsed)

        return events

    def _parse_betpawa_event(self, data: dict) -> dict | None:
        """Parse a BetPawa event into standard format.

        Args:
            data: Raw event data from BetPawa API.

        Returns:
            Standardized event dict, or None if cannot parse.
        """
        # Extract SportRadar ID from widgets
        widgets = data.get("widgets", [])
        sportradar_id = None
        for widget in widgets:
            if widget.get("type") == "SPORTRADAR":
                sportradar_id = widget.get("id")
                break

        if not sportradar_id:
            # Cannot match without SportRadar ID
            return None

        # Extract participants
        participants = data.get("participants", [])
        home_team = ""
        away_team = ""
        for p in participants:
            position = p.get("position", 0)
            name = p.get("name", "")
            if position == 1:
                home_team = name
            elif position == 2:
                away_team = name

        if not home_team or not away_team:
            return None

        # Parse kickoff time
        start_time_str = data.get("startTime", "")
        try:
            # BetPawa uses ISO 8601 format
            kickoff = datetime.fromisoformat(
                start_time_str.replace("Z", "+00:00")
            )
            # Convert to naive UTC for database
            kickoff = kickoff.replace(tzinfo=None)
        except (ValueError, AttributeError):
            return None

        event_id = str(data.get("id", ""))
        event_name = data.get("name", f"{home_team} - {away_team}")

        # Extract competition info from event data
        # BetPawa events list includes competition in the response
        competition = data.get("competition", {})
        comp_name = competition.get("name", "Unknown")
        comp_id = competition.get("id")

        # Region/country info
        region = data.get("region", {})
        country = region.get("name")

        return {
            "sportradar_id": sportradar_id,
            "name": event_name,
            "home_team": home_team,
            "away_team": away_team,
            "kickoff": kickoff,
            "external_event_id": event_id,
            "event_url": f"https://www.betpawa.ng/event/{event_id}",
            "tournament": {
                "sportradar_id": str(comp_id) if comp_id else None,
                "name": comp_name,
                "sport_id": 1,  # Football
                "country": country,
            },
        }

    async def _scrape_sportybet(
        self,
        client: SportyBetClient,
        db: AsyncSession,
    ) -> list[dict]:
        """Scrape events from SportyBet via SportRadar ID lookup.

        Queries database for events with SportRadar IDs and fetches
        corresponding odds from SportyBet.

        Args:
            client: SportyBet API client.
            db: Async database session for event lookup.

        Returns:
            List of event dicts with raw_data for OddsSnapshot storage.
        """
        events: list[dict] = []

        # Query for upcoming events with SportRadar IDs
        result = await db.execute(
            select(Event).where(
                Event.sportradar_id.isnot(None),
                Event.kickoff > datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        db_events = result.scalars().all()

        logger.info(
            f"Found {len(db_events)} events with SportRadar IDs to fetch from SportyBet"
        )

        for event in db_events:
            # Convert SportRadar ID to SportyBet format
            sportybet_id = f"sr:match:{event.sportradar_id}"

            try:
                raw_data = await client.fetch_event(sportybet_id)

                events.append({
                    "sportradar_id": event.sportradar_id,
                    "external_event_id": sportybet_id,
                    "event_url": f"https://www.sportybet.com/ng/sport/match/{sportybet_id}",
                    "raw_data": raw_data,
                    "event": event,  # Keep reference to DB event
                })

            except InvalidEventIdError:
                # Event doesn't exist on SportyBet - skip
                logger.debug(
                    f"Event {event.sportradar_id} not found on SportyBet"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to fetch event {event.sportradar_id} from SportyBet: {e}"
                )

            # Rate limiting delay
            await asyncio.sleep(0.1)

        logger.info(f"Scraped {len(events)} events from SportyBet")
        return events

    async def _store_events(
        self,
        db: AsyncSession,
        platform: Platform,
        events: list[dict],
    ) -> None:
        """Store scraped events in the database.

        Uses EventMatchingService to upsert events with proper matching logic.
        For SportyBet, creates EventBookmaker links and OddsSnapshot records
        since events already exist from BetPawa scraping.

        Args:
            db: Database session.
            platform: Source platform.
            events: List of event dicts in standard format.
        """
        if not events:
            return

        # Get or create bookmaker
        bookmaker_id = await self._get_bookmaker_id(db, platform)
        if not bookmaker_id:
            logger.error(f"Failed to get bookmaker ID for {platform}")
            return

        service = EventMatchingService()

        if platform == Platform.SPORTYBET:
            # SportyBet events already exist - just create links and snapshots
            for event_data in events:
                event = event_data["event"]  # DB event reference

                # Create EventBookmaker link
                await service.upsert_event_bookmaker(
                    db=db,
                    event_id=event.id,
                    bookmaker_id=bookmaker_id,
                    external_event_id=event_data["external_event_id"],
                    event_url=event_data.get("event_url"),
                )

                # Create OddsSnapshot with raw response
                snapshot = OddsSnapshot(
                    event_id=event.id,
                    bookmaker_id=bookmaker_id,
                    raw_response=event_data.get("raw_data"),
                )
                db.add(snapshot)

            logger.info(
                f"Stored {len(events)} event links and snapshots for {platform}"
            )
            return

        # Use EventMatchingService to process events (BetPawa and Bet9ja)
        result = await service.process_scraped_events(
            db=db,
            platform=platform,
            bookmaker_id=bookmaker_id,
            events=events,
        )

        logger.info(
            f"Stored {result.new_events} new, {result.updated_events} updated "
            f"events for {platform} ({result.new_tournaments} new tournaments)"
        )

    async def check_all_health(self) -> dict[Platform, bool]:
        """Check health of all platforms concurrently.

        Returns:
            Dict mapping platform to health status.
        """
        tasks = [
            self._clients[platform].check_health()
            for platform in Platform
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            platform: (
                result if isinstance(result, bool) else False
            )
            for platform, result in zip(Platform, results)
        }

    async def _log_error(
        self,
        db: AsyncSession,
        scrape_run_id: int,
        platform: Platform,
        error: Exception,
        event_id: int | None = None,
    ) -> None:
        """Log scrape error to database.

        Args:
            db: Database session.
            scrape_run_id: ID of the current scrape run.
            platform: Platform that failed.
            error: Exception that occurred.
            event_id: Optional event ID if error was event-specific.
        """
        from src.db.models.scrape import ScrapeError

        bookmaker_id = await self._get_bookmaker_id(db, platform)
        error_type = type(error).__name__

        scrape_error = ScrapeError(
            scrape_run_id=scrape_run_id,
            bookmaker_id=bookmaker_id,
            event_id=event_id,
            error_type=error_type,
            error_message=str(error)[:1000],  # Truncate long messages
        )
        db.add(scrape_error)
        # Don't commit here - batch commit in scrape_all

    async def _get_bookmaker_id(
        self,
        db: AsyncSession,
        platform: Platform,
    ) -> int | None:
        """Get or create bookmaker record for platform.

        Args:
            db: Database session.
            platform: Platform to get bookmaker for.

        Returns:
            Bookmaker ID, or None if not found and creation failed.
        """
        from src.db.models.bookmaker import Bookmaker

        # Map platform to slug
        slug = platform.value.lower()

        result = await db.execute(
            select(Bookmaker).where(Bookmaker.slug == slug)
        )
        bookmaker = result.scalar_one_or_none()
        if bookmaker:
            return bookmaker.id

        # Create if not exists (first run scenario)
        base_urls = {
            Platform.SPORTYBET: "https://www.sportybet.com",
            Platform.BETPAWA: "https://www.betpawa.ng",
            Platform.BET9JA: "https://sports.bet9ja.com",
        }
        bookmaker = Bookmaker(
            name=platform.value.title(),
            slug=slug,
            base_url=base_urls.get(platform),
        )
        db.add(bookmaker)
        await db.flush()  # Get ID without committing
        return bookmaker.id
