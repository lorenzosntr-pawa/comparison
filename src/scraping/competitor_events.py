"""Competitor event scraping service for SportyBet and Bet9ja."""

import asyncio
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
    CompetitorSource,
    CompetitorTournament,
)
from src.db.models.event import Event
from src.market_mapping.mappers.bet9ja import map_bet9ja_odds_to_betpawa
from src.market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from src.market_mapping.types.errors import MappingError
from src.market_mapping.types.sportybet import SportybetMarket
from src.scraping.clients.bet9ja import Bet9jaClient
from src.scraping.clients.sportybet import SportyBetClient

log = structlog.get_logger(__name__)


class CompetitorEventScrapingService:
    """Scrapes events and odds from competitor platforms (SportyBet, Bet9ja).

    Uses competitor_tournaments as source for tournament IDs, then fetches
    all events from each tournament. Events are stored in competitor_events
    with odds snapshots in competitor_odds_snapshots/competitor_market_odds.
    """

    def __init__(
        self,
        sportybet_client: SportyBetClient,
        bet9ja_client: Bet9jaClient,
    ) -> None:
        """Initialize with API clients.

        Args:
            sportybet_client: SportyBet API client.
            bet9ja_client: Bet9ja API client.
        """
        self._sportybet_client = sportybet_client
        self._bet9ja_client = bet9ja_client

    async def _get_betpawa_event_by_sr_id(
        self,
        db: AsyncSession,
        sportradar_id: str,
    ) -> int | None:
        """Look up betpawa event ID by SportRadar ID.

        Args:
            db: Database session.
            sportradar_id: SportRadar ID to look up.

        Returns:
            Event ID if found, None otherwise.
        """
        result = await db.execute(
            select(Event.id).where(Event.sportradar_id == sportradar_id)
        )
        row = result.first()
        return row[0] if row else None

    async def _upsert_competitor_event(
        self,
        db: AsyncSession,
        source: CompetitorSource,
        tournament_id: int,
        sportradar_id: str,
        external_id: str,
        name: str,
        home_team: str,
        away_team: str,
        kickoff: datetime,
    ) -> tuple[CompetitorEvent, bool]:
        """Upsert a competitor event record.

        Args:
            db: Database session.
            source: Source platform.
            tournament_id: FK to competitor_tournaments.
            sportradar_id: SportRadar ID for cross-platform matching.
            external_id: Platform-specific event ID.
            name: Event name.
            home_team: Home team name.
            away_team: Away team name.
            kickoff: Event start time.

        Returns:
            Tuple of (CompetitorEvent, is_new).
        """
        # Look up existing by source + external_id
        result = await db.execute(
            select(CompetitorEvent).where(
                CompetitorEvent.source == source.value,
                CompetitorEvent.external_id == external_id,
            )
        )
        existing = result.scalar_one_or_none()

        # Look up betpawa event ID
        betpawa_event_id = await self._get_betpawa_event_by_sr_id(db, sportradar_id)

        if existing:
            # Update existing record
            existing.tournament_id = tournament_id
            existing.sportradar_id = sportradar_id
            existing.name = name
            existing.home_team = home_team
            existing.away_team = away_team
            existing.kickoff = kickoff
            existing.betpawa_event_id = betpawa_event_id
            return existing, False
        else:
            # Create new record
            event = CompetitorEvent(
                source=source.value,
                tournament_id=tournament_id,
                betpawa_event_id=betpawa_event_id,
                name=name,
                home_team=home_team,
                away_team=away_team,
                kickoff=kickoff,
                external_id=external_id,
                sportradar_id=sportradar_id,
            )
            db.add(event)
            await db.flush()
            return event, True

    def _parse_sportybet_event(
        self,
        event_data: dict,
        tournament_id: int,
    ) -> dict | None:
        """Parse a SportyBet event into standard format.

        Args:
            event_data: Raw event data from SportyBet API.
            tournament_id: FK to competitor_tournaments.

        Returns:
            Parsed event dict, or None if cannot parse.
        """
        # Extract SportRadar ID from eventId (format: "sr:match:12345678")
        event_id = event_data.get("eventId", "")
        if not event_id.startswith("sr:match:"):
            return None

        # Extract numeric ID
        sportradar_id = event_id.replace("sr:match:", "")
        if not sportradar_id:
            return None

        # Extract team names
        home_team = event_data.get("homeTeamName", "")
        away_team = event_data.get("awayTeamName", "")
        if not home_team or not away_team:
            return None

        # Parse kickoff time (estimateStartTime is Unix timestamp in ms)
        estimate_start = event_data.get("estimateStartTime")
        if not estimate_start:
            return None

        try:
            kickoff = datetime.fromtimestamp(estimate_start / 1000, tz=timezone.utc)
            # Convert to naive UTC for database
            kickoff = kickoff.replace(tzinfo=None)
        except (ValueError, TypeError):
            return None

        return {
            "tournament_id": tournament_id,
            "sportradar_id": sportradar_id,
            "external_id": event_id,
            "name": f"{home_team} - {away_team}",
            "home_team": home_team,
            "away_team": away_team,
            "kickoff": kickoff,
            "markets": event_data.get("markets", []),
        }

    def _parse_bet9ja_event(
        self,
        event_data: dict,
        tournament_id: int,
    ) -> dict | None:
        """Parse a Bet9ja event into standard format.

        Args:
            event_data: Raw event data from Bet9ja API.
            tournament_id: FK to competitor_tournaments.

        Returns:
            Parsed event dict, or None if cannot parse.
        """
        # Extract SportRadar ID from EXTID field
        ext_id = event_data.get("EXTID")
        if not ext_id:
            return None

        # Parse home/away teams from DS field (format: "Home Team - Away Team")
        ds_field = event_data.get("DS", "")
        if " - " not in ds_field:
            return None

        parts = ds_field.split(" - ", 1)
        home_team = parts[0].strip()
        away_team = parts[1].strip() if len(parts) > 1 else ""
        if not home_team or not away_team:
            return None

        # Parse kickoff from STARTDATE (format: "YYYY-MM-DD HH:MM:SS")
        start_date_str = event_data.get("STARTDATE", "")
        try:
            kickoff = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None

        # Extract event ID
        event_id = str(event_data.get("C", ""))
        if not event_id:
            return None

        return {
            "tournament_id": tournament_id,
            "sportradar_id": ext_id,
            "external_id": event_id,
            "name": ds_field,
            "home_team": home_team,
            "away_team": away_team,
            "kickoff": kickoff,
            "odds": event_data.get("O", {}),
        }

    def _parse_sportybet_markets(
        self,
        markets: list[dict],
    ) -> list[CompetitorMarketOdds]:
        """Parse SportyBet markets into CompetitorMarketOdds records.

        Args:
            markets: List of market dicts from SportyBet API.

        Returns:
            List of CompetitorMarketOdds objects (snapshot_id not set).
        """
        market_odds_list: list[CompetitorMarketOdds] = []

        for market_data in markets:
            try:
                # Parse into Pydantic model
                sportybet_market = SportybetMarket.model_validate(market_data)

                # Map to Betpawa format
                mapped = map_sportybet_to_betpawa(sportybet_market)

                # Convert to CompetitorMarketOdds
                outcomes = [
                    {
                        "name": o.betpawa_outcome_name,
                        "odds": o.odds,
                        "is_active": o.is_active,
                    }
                    for o in mapped.outcomes
                ]

                market_odds = CompetitorMarketOdds(
                    betpawa_market_id=mapped.betpawa_market_id,
                    betpawa_market_name=mapped.betpawa_market_name,
                    line=mapped.line,
                    handicap_type=mapped.handicap.type if mapped.handicap else None,
                    handicap_home=mapped.handicap.home if mapped.handicap else None,
                    handicap_away=mapped.handicap.away if mapped.handicap else None,
                    outcomes=outcomes,
                )
                market_odds_list.append(market_odds)

            except MappingError:
                # Market not mappable - skip it (common for exotic markets)
                pass
            except Exception as e:
                log.debug("Error parsing SportyBet market", error=str(e))

        return market_odds_list

    def _parse_bet9ja_markets(
        self,
        odds_dict: dict,
    ) -> list[CompetitorMarketOdds]:
        """Parse Bet9ja odds into CompetitorMarketOdds records.

        Args:
            odds_dict: Odds dict from Bet9ja API (e.g., {"S_1X2_1": "1.50"}).

        Returns:
            List of CompetitorMarketOdds objects (snapshot_id not set).
        """
        market_odds_list: list[CompetitorMarketOdds] = []

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

                market_odds = CompetitorMarketOdds(
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
            log.warning("Error parsing Bet9ja markets", error=str(e))

        return market_odds_list

    async def scrape_sportybet_events(
        self,
        db: AsyncSession,
        scrape_run_id: int | None = None,
    ) -> dict:
        """Scrape all SportyBet events from discovered tournaments.

        Args:
            db: Database session.
            scrape_run_id: Optional scrape run ID for tracking.

        Returns:
            Dict with counts: {new: N, updated: N, snapshots: N, markets: N}
        """
        log.info("Starting SportyBet event scraping")

        # Get all active SportyBet tournaments
        result = await db.execute(
            select(CompetitorTournament).where(
                CompetitorTournament.source == CompetitorSource.SPORTYBET.value,
                CompetitorTournament.deleted_at.is_(None),
            )
        )
        tournaments = result.scalars().all()

        log.info("Found SportyBet tournaments", count=len(tournaments))

        if not tournaments:
            return {"new": 0, "updated": 0, "snapshots": 0, "markets": 0}

        # Use semaphore to limit concurrent tournament fetches
        semaphore = asyncio.Semaphore(10)
        new_count = 0
        updated_count = 0
        snapshots_count = 0
        markets_count = 0

        async def process_tournament(tournament: CompetitorTournament) -> tuple[int, int, int, int]:
            """Process a single tournament with rate limiting."""
            async with semaphore:
                new = 0
                updated = 0
                snapshots = 0
                markets = 0

                try:
                    # Fetch events for this tournament
                    events = await self._sportybet_client.fetch_events_by_tournament(
                        tournament.external_id
                    )

                    for event_data in events:
                        parsed = self._parse_sportybet_event(event_data, tournament.id)
                        if not parsed:
                            continue

                        # Upsert event
                        event, is_new = await self._upsert_competitor_event(
                            db=db,
                            source=CompetitorSource.SPORTYBET,
                            tournament_id=parsed["tournament_id"],
                            sportradar_id=parsed["sportradar_id"],
                            external_id=parsed["external_id"],
                            name=parsed["name"],
                            home_team=parsed["home_team"],
                            away_team=parsed["away_team"],
                            kickoff=parsed["kickoff"],
                        )

                        if is_new:
                            new += 1
                        else:
                            updated += 1

                        # Create odds snapshot
                        snapshot = CompetitorOddsSnapshot(
                            competitor_event_id=event.id,
                            scrape_run_id=scrape_run_id,
                            raw_response=event_data,
                        )
                        db.add(snapshot)
                        await db.flush()
                        snapshots += 1

                        # Parse and store markets
                        market_odds_list = self._parse_sportybet_markets(
                            parsed["markets"]
                        )
                        for market_odds in market_odds_list:
                            market_odds.snapshot_id = snapshot.id
                            db.add(market_odds)
                        markets += len(market_odds_list)

                except Exception as e:
                    log.warning(
                        "Failed to scrape SportyBet tournament",
                        tournament_id=tournament.external_id,
                        tournament_name=tournament.name,
                        error=str(e),
                    )

                return new, updated, snapshots, markets

        # Process all tournaments concurrently
        results = await asyncio.gather(
            *[process_tournament(t) for t in tournaments],
            return_exceptions=True,
        )

        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                new_count += result[0]
                updated_count += result[1]
                snapshots_count += result[2]
                markets_count += result[3]

        await db.commit()

        log.info(
            "Completed SportyBet event scraping",
            new=new_count,
            updated=updated_count,
            snapshots=snapshots_count,
            markets=markets_count,
        )

        return {
            "new": new_count,
            "updated": updated_count,
            "snapshots": snapshots_count,
            "markets": markets_count,
        }

    async def scrape_bet9ja_events(
        self,
        db: AsyncSession,
        scrape_run_id: int | None = None,
    ) -> dict:
        """Scrape all Bet9ja events from discovered tournaments.

        Args:
            db: Database session.
            scrape_run_id: Optional scrape run ID for tracking.

        Returns:
            Dict with counts: {new: N, updated: N, snapshots: N, markets: N}
        """
        log.info("Starting Bet9ja event scraping")

        # Get all active Bet9ja tournaments
        result = await db.execute(
            select(CompetitorTournament).where(
                CompetitorTournament.source == CompetitorSource.BET9JA.value,
                CompetitorTournament.deleted_at.is_(None),
            )
        )
        tournaments = result.scalars().all()

        log.info("Found Bet9ja tournaments", count=len(tournaments))

        if not tournaments:
            return {"new": 0, "updated": 0, "snapshots": 0, "markets": 0}

        # Use semaphore to limit concurrent tournament fetches
        semaphore = asyncio.Semaphore(10)
        new_count = 0
        updated_count = 0
        snapshots_count = 0
        markets_count = 0

        async def process_tournament(tournament: CompetitorTournament) -> tuple[int, int, int, int]:
            """Process a single tournament with rate limiting."""
            async with semaphore:
                new = 0
                updated = 0
                snapshots = 0
                markets = 0

                try:
                    # Fetch events for this tournament
                    events = await self._bet9ja_client.fetch_events(
                        tournament.external_id
                    )

                    for event_data in events:
                        parsed = self._parse_bet9ja_event(event_data, tournament.id)
                        if not parsed:
                            continue

                        # Upsert event
                        event, is_new = await self._upsert_competitor_event(
                            db=db,
                            source=CompetitorSource.BET9JA,
                            tournament_id=parsed["tournament_id"],
                            sportradar_id=parsed["sportradar_id"],
                            external_id=parsed["external_id"],
                            name=parsed["name"],
                            home_team=parsed["home_team"],
                            away_team=parsed["away_team"],
                            kickoff=parsed["kickoff"],
                        )

                        if is_new:
                            new += 1
                        else:
                            updated += 1

                        # Create odds snapshot
                        snapshot = CompetitorOddsSnapshot(
                            competitor_event_id=event.id,
                            scrape_run_id=scrape_run_id,
                            raw_response=event_data,
                        )
                        db.add(snapshot)
                        await db.flush()
                        snapshots += 1

                        # Parse and store markets
                        market_odds_list = self._parse_bet9ja_markets(parsed["odds"])
                        for market_odds in market_odds_list:
                            market_odds.snapshot_id = snapshot.id
                            db.add(market_odds)
                        markets += len(market_odds_list)

                except Exception as e:
                    log.warning(
                        "Failed to scrape Bet9ja tournament",
                        tournament_id=tournament.external_id,
                        tournament_name=tournament.name,
                        error=str(e),
                    )

                return new, updated, snapshots, markets

        # Process all tournaments concurrently
        results = await asyncio.gather(
            *[process_tournament(t) for t in tournaments],
            return_exceptions=True,
        )

        # Aggregate results
        for result in results:
            if isinstance(result, tuple):
                new_count += result[0]
                updated_count += result[1]
                snapshots_count += result[2]
                markets_count += result[3]

        await db.commit()

        log.info(
            "Completed Bet9ja event scraping",
            new=new_count,
            updated=updated_count,
            snapshots=snapshots_count,
            markets=markets_count,
        )

        return {
            "new": new_count,
            "updated": updated_count,
            "snapshots": snapshots_count,
            "markets": markets_count,
        }

    async def scrape_all(
        self,
        db: AsyncSession,
        scrape_run_id: int | None = None,
    ) -> dict:
        """Scrape events from all competitor platforms.

        Handles partial failures - one platform can fail while other continues.

        Args:
            db: Database session.
            scrape_run_id: Optional scrape run ID for tracking.

        Returns:
            Dict with results per platform:
            {
                "sportybet": {new: N, updated: N, snapshots: N, markets: N, error: None},
                "bet9ja": {new: N, updated: N, snapshots: N, markets: N, error: None},
            }
        """
        log.info("Starting competitor event scraping for all platforms")

        results: dict = {
            "sportybet": {"new": 0, "updated": 0, "snapshots": 0, "markets": 0, "error": None},
            "bet9ja": {"new": 0, "updated": 0, "snapshots": 0, "markets": 0, "error": None},
        }

        # Scrape SportyBet
        try:
            sportybet_result = await self.scrape_sportybet_events(db, scrape_run_id)
            results["sportybet"].update(sportybet_result)
        except Exception as e:
            log.error("SportyBet event scraping failed", error=str(e))
            results["sportybet"]["error"] = str(e)

        # Scrape Bet9ja
        try:
            bet9ja_result = await self.scrape_bet9ja_events(db, scrape_run_id)
            results["bet9ja"].update(bet9ja_result)
        except Exception as e:
            log.error("Bet9ja event scraping failed", error=str(e))
            results["bet9ja"]["error"] = str(e)

        log.info("Completed competitor event scraping for all platforms", results=results)
        return results
