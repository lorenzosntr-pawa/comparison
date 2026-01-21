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
from src.db.models.odds import MarketOdds, OddsSnapshot
from market_mapping.mappers.bet9ja import map_bet9ja_odds_to_betpawa
from market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from market_mapping.types.errors import MappingError
from market_mapping.types.sportybet import SportybetMarket
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
                    await db.rollback()  # Clear any failed transaction state
                    await self._log_error(db, scrape_run_id, platform, result)

                # Handle TimeoutError specially (str(TimeoutError()) returns empty in Python 3.11+)
                if isinstance(result, (TimeoutError, asyncio.TimeoutError)):
                    error_message = f"Platform scrape timed out after {timeout}s - too many competitions or slow network"
                else:
                    error_message = str(result) or f"Unknown error: {type(result).__name__}"

                platform_results.append(
                    PlatformResult(
                        platform=platform,
                        success=False,
                        events_count=0,
                        error_message=error_message,
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
                        if scrape_run_id and db:
                            await db.rollback()  # Clear failed transaction state
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
        # BetPawa API returns {"withRegions": [{"category": {...}, "regions": [...]}]}
        with_regions = categories_data.get("withRegions", [])
        if not with_regions:
            return competition_ids

        regions = with_regions[0].get("regions", [])

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

        Fetches the event list first, then fetches full event data
        (including markets) for each event.

        Args:
            client: BetPawa API client.
            competition_id: Competition ID to scrape.

        Returns:
            List of event dicts in standard format with raw_data for odds.
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
                # Fetch full event data with markets
                event_id = parsed["external_event_id"]
                try:
                    full_event_data = await client.fetch_event(event_id)
                    parsed["raw_data"] = full_event_data
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch full BetPawa event {event_id}: {e}"
                    )
                    # Still include event without raw_data
                events.append(parsed)
                # Rate limiting delay
                await asyncio.sleep(0.1)

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
        corresponding odds from SportyBet using parallel requests.

        Args:
            client: SportyBet API client.
            db: Async database session for event lookup.

        Returns:
            List of event dicts with raw_data for OddsSnapshot storage.
        """
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

        if not db_events:
            return []

        # Use semaphore to limit concurrent requests (10 parallel)
        semaphore = asyncio.Semaphore(10)

        async def fetch_single(event: Event) -> dict | None:
            """Fetch single event with rate limiting."""
            async with semaphore:
                sportybet_id = f"sr:match:{event.sportradar_id}"
                try:
                    raw_data = await client.fetch_event(sportybet_id)
                    return {
                        "sportradar_id": event.sportradar_id,
                        "external_event_id": sportybet_id,
                        "event_url": f"https://www.sportybet.com/ng/sport/match/{sportybet_id}",
                        "raw_data": raw_data,
                        "event": event,
                    }
                except InvalidEventIdError:
                    logger.debug(
                        f"Event {event.sportradar_id} not found on SportyBet"
                    )
                    return None
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch event {event.sportradar_id} from SportyBet: {e}"
                    )
                    return None
                finally:
                    # Small delay after each request for rate limiting
                    await asyncio.sleep(0.05)

        # Fetch all events in parallel (limited by semaphore)
        results = await asyncio.gather(
            *[fetch_single(event) for event in db_events],
            return_exceptions=True,
        )

        # Filter out None results and exceptions
        events = [r for r in results if r is not None and not isinstance(r, Exception)]

        logger.info(f"Scraped {len(events)} events from SportyBet")
        return events

    def _extract_football_tournaments(self, sports_data: dict) -> list[str]:
        """Extract football tournament IDs from GetSports response.

        Args:
            sports_data: Full API response from fetch_sports().

        Returns:
            List of tournament/group IDs for football.
        """
        tournament_ids: list[str] = []

        try:
            # Navigate: D.PAL.1.SG (Sport ID 1 = Soccer)
            d_data = sports_data.get("D", {})
            pal_data = d_data.get("PAL", {})
            soccer_data = pal_data.get("1", {})  # Sport ID 1 = Soccer
            sport_groups = soccer_data.get("SG", {})

            # SG contains groups keyed by ID, each with G dict of sub-groups
            for group_id, group_data in sport_groups.items():
                if not isinstance(group_data, dict):
                    continue

                # Each group can have sub-groups in G dict
                sub_groups = group_data.get("G", {})
                if isinstance(sub_groups, dict):
                    for sub_group_id in sub_groups.keys():
                        tournament_ids.append(str(sub_group_id))

                # The group itself may also be a tournament
                if "G" not in group_data or not group_data.get("G"):
                    # Leaf node - use the group_id itself
                    tournament_ids.append(str(group_id))

        except (AttributeError, TypeError) as e:
            logger.warning(f"Error parsing Bet9ja sports structure: {e}")

        return tournament_ids

    async def _scrape_bet9ja(
        self,
        client: Bet9jaClient,
        db: AsyncSession,
    ) -> list[dict]:
        """Scrape events from Bet9ja via tournament discovery.

        Discovers football tournaments and fetches events from each,
        matching via EXTID (SportRadar ID) field.

        Args:
            client: Bet9ja API client.
            db: Async database session (used for event matching).

        Returns:
            List of event dicts in standard format for EventMatchingService.
        """
        events: list[dict] = []

        # Discover football tournaments
        try:
            sports_data = await client.fetch_sports()
            tournament_ids = self._extract_football_tournaments(sports_data)
        except Exception as e:
            logger.error(f"Failed to fetch Bet9ja sports structure: {e}")
            return events

        logger.info(f"Discovered {len(tournament_ids)} Bet9ja football tournaments")

        for tournament_id in tournament_ids:
            try:
                tournament_events = await client.fetch_events(tournament_id)

                for event_data in tournament_events:
                    parsed = self._parse_bet9ja_event(event_data, tournament_id)
                    if parsed:
                        events.append(parsed)

            except Exception as e:
                logger.warning(
                    f"Failed to scrape Bet9ja tournament {tournament_id}: {e}"
                )
                # Continue with other tournaments

            # Rate limiting delay
            await asyncio.sleep(0.2)

        logger.info(f"Scraped {len(events)} events from Bet9ja")
        return events

    def _parse_bet9ja_event(
        self,
        data: dict,
        tournament_id: str,
    ) -> dict | None:
        """Parse a Bet9ja event into standard format.

        Args:
            data: Raw event data from Bet9ja API.
            tournament_id: Tournament ID for context.

        Returns:
            Standardized event dict, or None if cannot parse.
        """
        # Extract SportRadar ID from EXTID field
        ext_id = data.get("EXTID")
        if not ext_id:
            # Cannot match without SportRadar ID - skip gracefully
            logger.debug(
                f"Bet9ja event {data.get('C', 'unknown')} has no EXTID - skipping"
            )
            return None

        # Parse home/away teams from DS field (format: "Home Team - Away Team")
        ds_field = data.get("DS", "")
        if " - " in ds_field:
            parts = ds_field.split(" - ", 1)
            home_team = parts[0].strip()
            away_team = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Cannot parse teams
            return None

        if not home_team or not away_team:
            return None

        # Parse kickoff from STARTDATE (format: "YYYY-MM-DD HH:MM:SS")
        start_date_str = data.get("STARTDATE", "")
        try:
            kickoff = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None

        # Extract event ID and URL
        event_id = str(data.get("C", ""))
        if not event_id:
            return None

        # Tournament info from the event data
        # Bet9ja events have G (group/tournament) and GDS (group display name)
        tournament_name = data.get("GDS", "Unknown")
        # Country info may be in parent group - use tournament_id as fallback
        group_id = data.get("G")

        return {
            "sportradar_id": ext_id,
            "name": ds_field,
            "home_team": home_team,
            "away_team": away_team,
            "kickoff": kickoff,
            "external_event_id": event_id,
            "event_url": f"https://sports.bet9ja.com/sport/match/{event_id}",
            "raw_data": data,  # Store raw response for OddsSnapshot
            "tournament": {
                "sportradar_id": str(group_id) if group_id else None,
                "name": tournament_name,
                "sport_id": 1,  # Football
                "country": None,  # Not available in event data
            },
        }

    def _parse_sportybet_markets(self, raw_data: dict) -> list[MarketOdds]:
        """Parse SportyBet raw response into MarketOdds records.

        Args:
            raw_data: Raw API response from SportyBet (event data).

        Returns:
            List of MarketOdds objects ready to add to a snapshot.
        """
        market_odds_list = []
        markets = raw_data.get("markets", [])

        for market_data in markets:
            try:
                # Parse into Pydantic model
                sportybet_market = SportybetMarket.model_validate(market_data)

                # Map to Betpawa format
                mapped = map_sportybet_to_betpawa(sportybet_market)

                # Convert MappedMarket to MarketOdds
                outcomes = [
                    {
                        "name": o.betpawa_outcome_name,
                        "odds": o.odds,
                        "is_active": o.is_active,
                    }
                    for o in mapped.outcomes
                ]

                market_odds = MarketOdds(
                    betpawa_market_id=mapped.betpawa_market_id,
                    betpawa_market_name=mapped.betpawa_market_name,
                    line=mapped.line,
                    handicap_type=mapped.handicap.type if mapped.handicap else None,
                    handicap_home=mapped.handicap.home if mapped.handicap else None,
                    handicap_away=mapped.handicap.away if mapped.handicap else None,
                    outcomes=outcomes,
                )
                market_odds_list.append(market_odds)

            except MappingError as e:
                # Market not mappable - skip it (common for exotic markets)
                logger.debug(f"Could not map SportyBet market: {e}")
            except Exception as e:
                logger.warning(f"Error parsing SportyBet market: {e}")

        return market_odds_list

    def _parse_bet9ja_markets(self, raw_data: dict) -> list[MarketOdds]:
        """Parse Bet9ja raw response into MarketOdds records.

        Args:
            raw_data: Raw API response from Bet9ja (event data).

        Returns:
            List of MarketOdds objects ready to add to a snapshot.
        """
        market_odds_list = []

        # Bet9ja odds are nested inside the "O" object
        # e.g., {"O": {"S_1X2_1": "2.18", "S_1X2_2": "3.25", ...}}
        odds_dict = raw_data.get("O", {})

        if not odds_dict or not isinstance(odds_dict, dict):
            return market_odds_list

        try:
            # Map all odds at once
            mapped_markets = map_bet9ja_odds_to_betpawa(odds_dict)

            for mapped in mapped_markets:
                outcomes = [
                    {
                        "name": o.betpawa_outcome_name,
                        "odds": o.odds,
                        "is_active": o.is_active,
                    }
                    for o in mapped.outcomes
                ]

                market_odds = MarketOdds(
                    betpawa_market_id=mapped.betpawa_market_id,
                    betpawa_market_name=mapped.betpawa_market_name,
                    line=mapped.line,
                    handicap_type=mapped.handicap.type if mapped.handicap else None,
                    handicap_home=mapped.handicap.home if mapped.handicap else None,
                    handicap_away=mapped.handicap.away if mapped.handicap else None,
                    outcomes=outcomes,
                )
                market_odds_list.append(market_odds)

        except Exception as e:
            logger.warning(f"Error parsing Bet9ja markets: {e}")

        return market_odds_list

    def _parse_betpawa_markets(self, raw_data: dict) -> list[MarketOdds]:
        """Parse BetPawa raw response into MarketOdds records.

        BetPawa markets ARE the canonical format - no mapping needed.
        Direct extraction from the markets array.

        Args:
            raw_data: Raw API response from BetPawa (full event data).

        Returns:
            List of MarketOdds objects ready to add to a snapshot.
        """
        market_odds_list = []
        markets = raw_data.get("markets", [])

        for market_data in markets:
            market_type = market_data.get("marketType", {})
            market_id = market_type.get("id")

            if not market_id:
                continue

            for row in market_data.get("row", []):
                prices = row.get("prices", [])
                line = row.get("formattedHandicap")

                # Parse line to float if present
                # Try row.formattedHandicap first, then fall back to prices[0].handicap
                line_value = None
                if line:
                    try:
                        line_value = float(line)
                    except (ValueError, TypeError):
                        line_value = None

                if line_value is None and prices:
                    # Fall back to handicap from first price (common for O/U markets)
                    price_handicap = prices[0].get("handicap")
                    if price_handicap:
                        try:
                            line_value = float(price_handicap)
                        except (ValueError, TypeError):
                            line_value = None

                outcomes = [
                    {
                        "name": p.get("name"),
                        "odds": p.get("price"),
                        "is_active": not p.get("suspended", False),
                    }
                    for p in prices
                    if p.get("name") and p.get("price")
                ]

                if not outcomes:
                    continue

                market_odds = MarketOdds(
                    betpawa_market_id=str(market_id),
                    betpawa_market_name=market_type.get("displayName", ""),
                    line=line_value,
                    outcomes=outcomes,
                )
                market_odds_list.append(market_odds)

        return market_odds_list

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
            markets_count = 0
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
                await db.flush()  # Get snapshot ID

                # Parse markets from raw response
                raw_data = event_data.get("raw_data")
                if raw_data:
                    market_odds = self._parse_sportybet_markets(raw_data)
                    for mo in market_odds:
                        mo.snapshot_id = snapshot.id
                        db.add(mo)
                    markets_count += len(market_odds)

            logger.info(
                f"Stored {len(events)} event links and {markets_count} markets for {platform}"
            )
            return

        if platform == Platform.BET9JA:
            # Bet9ja events may be new - use full EventMatchingService flow
            # Then create OddsSnapshot for each event
            result = await service.process_scraped_events(
                db=db,
                platform=platform,
                bookmaker_id=bookmaker_id,
                events=events,
            )

            # Create OddsSnapshot records with raw responses
            # Need to look up event IDs by sportradar_id
            sportradar_ids = [e["sportradar_id"] for e in events]
            events_map = await service.get_events_by_sportradar_ids(
                db, sportradar_ids
            )

            markets_count = 0
            for event_data in events:
                event = events_map.get(event_data["sportradar_id"])
                if event and event_data.get("raw_data"):
                    snapshot = OddsSnapshot(
                        event_id=event.id,
                        bookmaker_id=bookmaker_id,
                        raw_response=event_data["raw_data"],
                    )
                    db.add(snapshot)
                    await db.flush()  # Get snapshot ID

                    # Parse markets from raw response
                    market_odds = self._parse_bet9ja_markets(event_data["raw_data"])
                    for mo in market_odds:
                        mo.snapshot_id = snapshot.id
                        db.add(mo)
                    markets_count += len(market_odds)

            logger.info(
                f"Stored {result.new_events} new, {result.updated_events} updated "
                f"events for {platform} ({result.new_tournaments} new tournaments, "
                f"{len(events)} snapshots, {markets_count} markets)"
            )
            return

        # Use EventMatchingService to process events (BetPawa)
        result = await service.process_scraped_events(
            db=db,
            platform=platform,
            bookmaker_id=bookmaker_id,
            events=events,
        )

        # Create OddsSnapshot records with raw responses for BetPawa
        # Need to look up event IDs by sportradar_id
        sportradar_ids = [e["sportradar_id"] for e in events if e.get("raw_data")]
        events_map = await service.get_events_by_sportradar_ids(
            db, sportradar_ids
        )

        markets_count = 0
        snapshots_count = 0
        for event_data in events:
            event = events_map.get(event_data["sportradar_id"])
            if event and event_data.get("raw_data"):
                snapshot = OddsSnapshot(
                    event_id=event.id,
                    bookmaker_id=bookmaker_id,
                    raw_response=event_data["raw_data"],
                )
                db.add(snapshot)
                await db.flush()  # Get snapshot ID

                # Parse markets from raw response (BetPawa is canonical - direct extraction)
                market_odds = self._parse_betpawa_markets(event_data["raw_data"])
                for mo in market_odds:
                    mo.snapshot_id = snapshot.id
                    db.add(mo)
                markets_count += len(market_odds)
                snapshots_count += 1

        logger.info(
            f"Stored {result.new_events} new, {result.updated_events} updated "
            f"events for {platform} ({result.new_tournaments} new tournaments, "
            f"{snapshots_count} snapshots, {markets_count} markets)"
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
