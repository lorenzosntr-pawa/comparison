"""Competitor event scraping service for SportyBet and Bet9ja.

Refactored to use fetch-then-store pattern to avoid SQLAlchemy session concurrency issues.
All API calls happen in parallel (Phase 1), then all DB writes happen sequentially (Phase 2).
"""

import asyncio
from datetime import datetime, timezone
from typing import Any

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
from src.scraping.exceptions import ApiError, InvalidEventIdError, NetworkError

log = structlog.get_logger(__name__)


class CompetitorEventScrapingService:
    """Scrapes events and odds from competitor platforms (SportyBet, Bet9ja).

    Uses competitor_tournaments as source for tournament IDs, then fetches
    all events from each tournament. Events are stored in competitor_events
    with odds snapshots in competitor_odds_snapshots/competitor_market_odds.

    Architecture: Fetch-then-Store pattern
    - Phase 1 (API only): Parallel API calls, collect all data in memory
    - Phase 2 (DB only): Sequential DB writes with single session
    This avoids SQLAlchemy async session concurrency issues.
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
            "raw_response": event_data,
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

        # Extract event ID - use "ID" for GetEvent API calls, not "C" (short code)
        event_id = str(event_data.get("ID", ""))
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
            "raw_response": event_data,
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

    async def _fetch_full_sportybet_odds(
        self,
        event_id: str,
    ) -> dict | None:
        """Fetch full event details from SportyBet.

        Args:
            event_id: SportRadar event ID (e.g., "sr:match:61300947").

        Returns:
            Full event data dict with all markets, or None on error.
        """
        try:
            return await self._sportybet_client.fetch_event(event_id)
        except (InvalidEventIdError, NetworkError, ApiError) as e:
            log.debug(
                "Failed to fetch full SportyBet event",
                event_id=event_id,
                error=str(e),
            )
            return None
        except Exception as e:
            log.warning(
                "Unexpected error fetching full SportyBet event",
                event_id=event_id,
                error=str(e),
            )
            return None

    async def _fetch_full_bet9ja_odds(
        self,
        event_id: str,
    ) -> dict | None:
        """Fetch full event details from Bet9ja.

        Args:
            event_id: Bet9ja event ID (e.g., "707096003").

        Returns:
            Full event data dict with all odds, or None on error.
        """
        try:
            return await self._bet9ja_client.fetch_event(event_id)
        except (InvalidEventIdError, NetworkError, ApiError) as e:
            log.debug(
                "Failed to fetch full Bet9ja event",
                event_id=event_id,
                error=str(e),
            )
            return None
        except Exception as e:
            log.warning(
                "Unexpected error fetching full Bet9ja event",
                event_id=event_id,
                error=str(e),
            )
            return None

    # =========================================================================
    # FETCH-THEN-STORE PATTERN: SportyBet
    # =========================================================================

    async def _fetch_sportybet_tournaments(self) -> list[dict]:
        """Fetch list of active SportyBet tournaments from database.

        Note: This is a lightweight DB read done before parallel API calls.
        Returns list of dicts with tournament info needed for API calls.
        """
        # This will be called with a fresh session in the main method
        return []  # Placeholder - actual implementation reads from caller's session

    async def _fetch_sportybet_events_api_only(
        self,
        tournaments: list[CompetitorTournament],
        scrape_run_id: int | None = None,
    ) -> list[dict]:
        """Phase 1: Fetch all SportyBet events via API (no DB writes).

        Args:
            tournaments: List of tournaments to scrape.
            scrape_run_id: Optional scrape run ID for tracking.

        Returns:
            List of dicts containing parsed event data and raw responses.
        """
        log.info(
            "Phase 1: Fetching SportyBet events (API only)",
            tournament_count=len(tournaments),
        )

        semaphore = asyncio.Semaphore(10)
        all_events: list[dict] = []

        async def fetch_tournament(tournament: CompetitorTournament) -> list[dict]:
            """Fetch events from a single tournament (API only)."""
            async with semaphore:
                try:
                    events = await self._sportybet_client.fetch_events_by_tournament(
                        tournament.external_id
                    )
                    parsed_events = []
                    for event_data in events:
                        parsed = self._parse_sportybet_event(event_data, tournament.id)
                        if parsed:
                            parsed_events.append(parsed)
                    return parsed_events
                except Exception as e:
                    log.warning(
                        "Failed to fetch SportyBet tournament",
                        tournament_id=tournament.external_id,
                        tournament_name=tournament.name,
                        error=str(e),
                    )
                    return []

        # Parallel API calls
        results = await asyncio.gather(
            *[fetch_tournament(t) for t in tournaments],
            return_exceptions=True,
        )

        # Collect all events
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)

        log.info(
            "Phase 1 complete: Fetched SportyBet events",
            total_events=len(all_events),
        )
        return all_events

    async def _store_sportybet_events_sequential(
        self,
        db: AsyncSession,
        events_data: list[dict],
        scrape_run_id: int | None = None,
    ) -> tuple[dict, list[int]]:
        """Phase 2: Store SportyBet events in database (sequential, no concurrency).

        Args:
            db: Database session.
            events_data: List of parsed event dicts from Phase 1.
            scrape_run_id: Optional scrape run ID for tracking.

        Returns:
            Tuple of (counts dict, list of snapshot IDs for full odds fetch).
        """
        log.info(
            "Phase 2: Storing SportyBet events (DB sequential)",
            event_count=len(events_data),
        )

        new_count = 0
        updated_count = 0
        snapshots_count = 0
        snapshot_ids: list[int] = []

        # Sequential processing - no concurrency
        for event_dict in events_data:
            try:
                # Upsert event
                event, is_new = await self._upsert_competitor_event(
                    db=db,
                    source=CompetitorSource.SPORTYBET,
                    tournament_id=event_dict["tournament_id"],
                    sportradar_id=event_dict["sportradar_id"],
                    external_id=event_dict["external_id"],
                    name=event_dict["name"],
                    home_team=event_dict["home_team"],
                    away_team=event_dict["away_team"],
                    kickoff=event_dict["kickoff"],
                )

                if is_new:
                    new_count += 1
                else:
                    updated_count += 1

                # Create odds snapshot
                snapshot = CompetitorOddsSnapshot(
                    competitor_event_id=event.id,
                    scrape_run_id=scrape_run_id,
                    raw_response=event_dict["raw_response"],
                )
                db.add(snapshot)
                await db.flush()
                snapshots_count += 1
                snapshot_ids.append(snapshot.id)

            except Exception as e:
                log.warning(
                    "Failed to store SportyBet event",
                    event_name=event_dict.get("name"),
                    error=str(e),
                )

        await db.commit()

        log.info(
            "Phase 2 complete: Stored SportyBet events",
            new=new_count,
            updated=updated_count,
            snapshots=snapshots_count,
        )

        return {
            "new": new_count,
            "updated": updated_count,
            "snapshots": snapshots_count,
        }, snapshot_ids

    # =========================================================================
    # FETCH-THEN-STORE PATTERN: Bet9ja
    # =========================================================================

    async def _fetch_bet9ja_events_api_only(
        self,
        tournaments: list[CompetitorTournament],
        scrape_run_id: int | None = None,
    ) -> list[dict]:
        """Phase 1: Fetch all Bet9ja events via API (no DB writes).

        Args:
            tournaments: List of tournaments to scrape.
            scrape_run_id: Optional scrape run ID for tracking.

        Returns:
            List of dicts containing parsed event data and raw responses.
        """
        log.info(
            "Phase 1: Fetching Bet9ja events (API only)",
            tournament_count=len(tournaments),
        )

        semaphore = asyncio.Semaphore(10)
        all_events: list[dict] = []

        async def fetch_tournament(tournament: CompetitorTournament) -> list[dict]:
            """Fetch events from a single tournament (API only)."""
            async with semaphore:
                try:
                    events = await self._bet9ja_client.fetch_events(
                        tournament.external_id
                    )
                    parsed_events = []
                    for event_data in events:
                        parsed = self._parse_bet9ja_event(event_data, tournament.id)
                        if parsed:
                            parsed_events.append(parsed)
                    return parsed_events
                except Exception as e:
                    log.warning(
                        "Failed to fetch Bet9ja tournament",
                        tournament_id=tournament.external_id,
                        tournament_name=tournament.name,
                        error=str(e),
                    )
                    return []

        # Parallel API calls
        results = await asyncio.gather(
            *[fetch_tournament(t) for t in tournaments],
            return_exceptions=True,
        )

        # Collect all events
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)

        log.info(
            "Phase 1 complete: Fetched Bet9ja events",
            total_events=len(all_events),
        )
        return all_events

    async def _store_bet9ja_events_sequential(
        self,
        db: AsyncSession,
        events_data: list[dict],
        scrape_run_id: int | None = None,
    ) -> tuple[dict, list[int]]:
        """Phase 2: Store Bet9ja events in database (sequential, no concurrency).

        Args:
            db: Database session.
            events_data: List of parsed event dicts from Phase 1.
            scrape_run_id: Optional scrape run ID for tracking.

        Returns:
            Tuple of (counts dict, list of snapshot IDs for full odds fetch).
        """
        log.info(
            "Phase 2: Storing Bet9ja events (DB sequential)",
            event_count=len(events_data),
        )

        new_count = 0
        updated_count = 0
        snapshots_count = 0
        snapshot_ids: list[int] = []

        # Sequential processing - no concurrency
        for event_dict in events_data:
            try:
                # Upsert event
                event, is_new = await self._upsert_competitor_event(
                    db=db,
                    source=CompetitorSource.BET9JA,
                    tournament_id=event_dict["tournament_id"],
                    sportradar_id=event_dict["sportradar_id"],
                    external_id=event_dict["external_id"],
                    name=event_dict["name"],
                    home_team=event_dict["home_team"],
                    away_team=event_dict["away_team"],
                    kickoff=event_dict["kickoff"],
                )

                if is_new:
                    new_count += 1
                else:
                    updated_count += 1

                # Create odds snapshot
                snapshot = CompetitorOddsSnapshot(
                    competitor_event_id=event.id,
                    scrape_run_id=scrape_run_id,
                    raw_response=event_dict["raw_response"],
                )
                db.add(snapshot)
                await db.flush()
                snapshots_count += 1
                snapshot_ids.append(snapshot.id)

            except Exception as e:
                log.warning(
                    "Failed to store Bet9ja event",
                    event_name=event_dict.get("name"),
                    error=str(e),
                )

        await db.commit()

        log.info(
            "Phase 2 complete: Stored Bet9ja events",
            new=new_count,
            updated=updated_count,
            snapshots=snapshots_count,
        )

        return {
            "new": new_count,
            "updated": updated_count,
            "snapshots": snapshots_count,
        }, snapshot_ids

    # =========================================================================
    # FETCH-THEN-STORE PATTERN: Full Odds
    # =========================================================================

    async def _fetch_full_odds_api_only(
        self,
        source: CompetitorSource,
        events_to_fetch: list[dict],
    ) -> list[dict]:
        """Phase 1: Fetch full odds for all events via API (no DB writes).

        Args:
            source: Platform source.
            events_to_fetch: List of dicts with {snapshot_id, external_id, raw_response}.

        Returns:
            List of dicts with {snapshot_id, external_id, full_data, error}.
        """
        log.info(
            "Phase 1: Fetching full odds (API only)",
            source=source.value,
            event_count=len(events_to_fetch),
        )

        # Use different concurrency limits per platform
        if source == CompetitorSource.SPORTYBET:
            semaphore = asyncio.Semaphore(30)
        else:
            semaphore = asyncio.Semaphore(10)

        results: list[dict] = []

        async def fetch_event(event_info: dict) -> dict:
            """Fetch full odds for a single event (API only)."""
            async with semaphore:
                snapshot_id = event_info["snapshot_id"]
                external_id = event_info["external_id"]

                try:
                    if source == CompetitorSource.SPORTYBET:
                        full_data = await self._fetch_full_sportybet_odds(external_id)
                    else:
                        # For Bet9ja, get correct ID from raw_response if needed
                        raw = event_info.get("raw_response") or {}
                        bet9ja_event_id = str(raw.get("ID", "")) or external_id
                        full_data = await self._fetch_full_bet9ja_odds(bet9ja_event_id)

                    return {
                        "snapshot_id": snapshot_id,
                        "external_id": external_id,
                        "full_data": full_data,
                        "error": None,
                    }
                except Exception as e:
                    return {
                        "snapshot_id": snapshot_id,
                        "external_id": external_id,
                        "full_data": None,
                        "error": str(e),
                    }

        # Process in batches
        batch_size = 100
        for i in range(0, len(events_to_fetch), batch_size):
            batch = events_to_fetch[i : i + batch_size]

            batch_results = await asyncio.gather(
                *[fetch_event(e) for e in batch],
                return_exceptions=True,
            )

            for result in batch_results:
                if isinstance(result, dict):
                    results.append(result)
                elif isinstance(result, Exception):
                    log.warning("Exception in full odds fetch", error=str(result))

            # Log progress
            log.info(
                "Full odds fetch progress (API)",
                source=source.value,
                processed=min(i + batch_size, len(events_to_fetch)),
                total=len(events_to_fetch),
            )

        log.info(
            "Phase 1 complete: Fetched full odds",
            source=source.value,
            fetched=len([r for r in results if r.get("full_data")]),
            errors=len([r for r in results if r.get("error")]),
        )
        return results

    async def _update_snapshots_with_odds_sequential(
        self,
        db: AsyncSession,
        source: CompetitorSource,
        fetch_results: list[dict],
    ) -> dict:
        """Phase 2: Update snapshots with full odds (DB sequential).

        Args:
            db: Database session.
            source: Platform source.
            fetch_results: Results from _fetch_full_odds_api_only.

        Returns:
            Dict with {events_processed, total_markets, errors}.
        """
        from sqlalchemy import delete

        log.info(
            "Phase 2: Updating snapshots with full odds (DB sequential)",
            source=source.value,
            result_count=len(fetch_results),
        )

        events_processed = 0
        total_markets = 0
        errors = 0

        # Sequential processing - no concurrency
        for result in fetch_results:
            snapshot_id = result["snapshot_id"]
            full_data = result.get("full_data")

            if not full_data:
                errors += 1
                continue

            try:
                # Get snapshot
                snap_result = await db.execute(
                    select(CompetitorOddsSnapshot, CompetitorEvent)
                    .join(
                        CompetitorEvent,
                        CompetitorOddsSnapshot.competitor_event_id == CompetitorEvent.id,
                    )
                    .where(CompetitorOddsSnapshot.id == snapshot_id)
                )
                row = snap_result.first()
                if not row:
                    errors += 1
                    continue

                snapshot, event = row

                # Delete existing market_odds
                await db.execute(
                    delete(CompetitorMarketOdds).where(
                        CompetitorMarketOdds.snapshot_id == snapshot.id
                    )
                )

                # Parse markets based on source
                if source == CompetitorSource.SPORTYBET:
                    markets = full_data.get("markets", [])
                    market_odds_list = self._parse_sportybet_markets(markets)
                else:
                    odds_dict = full_data.get("O", {})
                    market_odds_list = self._parse_bet9ja_markets(odds_dict)

                    # Update event.external_id if needed
                    correct_id = str(full_data.get("ID", ""))
                    if correct_id and event.external_id != correct_id:
                        event.external_id = correct_id

                # Add new market odds
                for market_odds in market_odds_list:
                    market_odds.snapshot_id = snapshot.id
                    db.add(market_odds)

                # Update snapshot raw_response
                snapshot.raw_response = full_data

                total_markets += len(market_odds_list)
                events_processed += 1

            except Exception as e:
                log.warning(
                    "Failed to update snapshot with full odds",
                    snapshot_id=snapshot_id,
                    error=str(e),
                )
                errors += 1

        await db.commit()

        log.info(
            "Phase 2 complete: Updated snapshots with full odds",
            source=source.value,
            events_processed=events_processed,
            total_markets=total_markets,
            errors=errors,
        )

        return {
            "events_processed": events_processed,
            "total_markets": total_markets,
            "errors": errors,
        }

    async def scrape_full_odds_for_events(
        self,
        db: AsyncSession,
        source: CompetitorSource,
        snapshot_ids: list[int],
    ) -> dict[str, Any]:
        """Fetch full odds for events using fetch-then-store pattern.

        Args:
            db: Database session.
            source: Platform source (SPORTYBET or BET9JA).
            snapshot_ids: List of snapshot IDs to enhance with full odds.

        Returns:
            Dict with stats: {events_processed: N, total_markets: N, errors: N}
        """
        if not snapshot_ids:
            return {"events_processed": 0, "total_markets": 0, "errors": 0}

        # Build list of events to fetch (need external_id and raw_response)
        events_to_fetch: list[dict] = []
        for snapshot_id in snapshot_ids:
            result = await db.execute(
                select(CompetitorOddsSnapshot, CompetitorEvent)
                .join(
                    CompetitorEvent,
                    CompetitorOddsSnapshot.competitor_event_id == CompetitorEvent.id,
                )
                .where(CompetitorOddsSnapshot.id == snapshot_id)
            )
            row = result.first()
            if row:
                snapshot, event = row
                events_to_fetch.append({
                    "snapshot_id": snapshot_id,
                    "external_id": event.external_id,
                    "raw_response": snapshot.raw_response,
                })

        # Phase 1: Fetch full odds (API only, parallel)
        fetch_results = await self._fetch_full_odds_api_only(source, events_to_fetch)

        # Phase 2: Update snapshots (DB only, sequential)
        return await self._update_snapshots_with_odds_sequential(db, source, fetch_results)

    # =========================================================================
    # PUBLIC API: Main scraping methods
    # =========================================================================

    async def scrape_sportybet_events(
        self,
        db: AsyncSession,
        scrape_run_id: int | None = None,
        fetch_full_odds: bool = True,
    ) -> dict:
        """Scrape all SportyBet events from discovered tournaments.

        Uses fetch-then-store pattern:
        - Phase 1: Fetch all events via API (parallel)
        - Phase 2: Store all events in DB (sequential)
        - Phase 3: Fetch full odds (parallel API, sequential DB)

        Args:
            db: Database session.
            scrape_run_id: Optional scrape run ID for tracking.
            fetch_full_odds: If True, fetch full market data for each event.

        Returns:
            Dict with counts: {new, updated, snapshots, markets, events_with_full_odds}
        """
        log.info("Starting SportyBet event scraping", fetch_full_odds=fetch_full_odds)

        # Get all active SportyBet tournaments (lightweight DB read)
        result = await db.execute(
            select(CompetitorTournament).where(
                CompetitorTournament.source == CompetitorSource.SPORTYBET.value,
                CompetitorTournament.deleted_at.is_(None),
            )
        )
        tournaments = list(result.scalars().all())

        # Ensure clean session state before long API phase
        # This commits any pending operations from previous phases
        await db.commit()

        log.info("Found SportyBet tournaments", count=len(tournaments))

        if not tournaments:
            return {
                "new": 0,
                "updated": 0,
                "snapshots": 0,
                "markets": 0,
                "events_with_full_odds": 0,
            }

        # Phase 1: Fetch all events (API only)
        events_data = await self._fetch_sportybet_events_api_only(
            tournaments, scrape_run_id
        )

        # Phase 2: Store all events (DB sequential)
        counts, snapshot_ids = await self._store_sportybet_events_sequential(
            db, events_data, scrape_run_id
        )

        # Commit after storage phase to ensure clean state for full odds phase
        await db.commit()

        # Phase 3: Fetch full odds (fetch-then-store)
        events_with_full_odds = 0
        markets_count = 0
        if fetch_full_odds and snapshot_ids:
            log.info(
                "Phase 3: Fetching full market data for SportyBet events",
                total_events=len(snapshot_ids),
            )
            full_odds_result = await self.scrape_full_odds_for_events(
                db, CompetitorSource.SPORTYBET, snapshot_ids
            )
            events_with_full_odds = full_odds_result["events_processed"]
            markets_count = full_odds_result["total_markets"]

            # Commit after full odds phase
            await db.commit()

        log.info(
            "Completed SportyBet event scraping",
            new=counts["new"],
            updated=counts["updated"],
            snapshots=counts["snapshots"],
            markets=markets_count,
            events_with_full_odds=events_with_full_odds,
        )

        return {
            "new": counts["new"],
            "updated": counts["updated"],
            "snapshots": counts["snapshots"],
            "markets": markets_count,
            "events_with_full_odds": events_with_full_odds,
        }

    async def scrape_bet9ja_events(
        self,
        db: AsyncSession,
        scrape_run_id: int | None = None,
        fetch_full_odds: bool = True,
    ) -> dict:
        """Scrape all Bet9ja events from discovered tournaments.

        Uses fetch-then-store pattern:
        - Phase 1: Fetch all events via API (parallel)
        - Phase 2: Store all events in DB (sequential)
        - Phase 3: Fetch full odds (parallel API, sequential DB)

        Args:
            db: Database session.
            scrape_run_id: Optional scrape run ID for tracking.
            fetch_full_odds: If True, fetch full market data for each event.

        Returns:
            Dict with counts: {new, updated, snapshots, markets, events_with_full_odds}
        """
        log.info("Starting Bet9ja event scraping", fetch_full_odds=fetch_full_odds)

        # Get all active Bet9ja tournaments (lightweight DB read)
        result = await db.execute(
            select(CompetitorTournament).where(
                CompetitorTournament.source == CompetitorSource.BET9JA.value,
                CompetitorTournament.deleted_at.is_(None),
            )
        )
        tournaments = list(result.scalars().all())

        # Ensure clean session state before long API phase
        # This commits any pending operations from previous phases
        await db.commit()

        log.info("Found Bet9ja tournaments", count=len(tournaments))

        if not tournaments:
            return {
                "new": 0,
                "updated": 0,
                "snapshots": 0,
                "markets": 0,
                "events_with_full_odds": 0,
            }

        # Phase 1: Fetch all events (API only)
        events_data = await self._fetch_bet9ja_events_api_only(
            tournaments, scrape_run_id
        )

        # Phase 2: Store all events (DB sequential)
        counts, snapshot_ids = await self._store_bet9ja_events_sequential(
            db, events_data, scrape_run_id
        )

        # Commit after storage phase to ensure clean state for full odds phase
        await db.commit()

        # Phase 3: Fetch full odds (fetch-then-store)
        events_with_full_odds = 0
        markets_count = 0
        if fetch_full_odds and snapshot_ids:
            log.info(
                "Phase 3: Fetching full market data for Bet9ja events",
                total_events=len(snapshot_ids),
            )
            full_odds_result = await self.scrape_full_odds_for_events(
                db, CompetitorSource.BET9JA, snapshot_ids
            )
            events_with_full_odds = full_odds_result["events_processed"]
            markets_count = full_odds_result["total_markets"]

            # Commit after full odds phase
            await db.commit()

        log.info(
            "Completed Bet9ja event scraping",
            new=counts["new"],
            updated=counts["updated"],
            snapshots=counts["snapshots"],
            markets=markets_count,
            events_with_full_odds=events_with_full_odds,
        )

        return {
            "new": counts["new"],
            "updated": counts["updated"],
            "snapshots": counts["snapshots"],
            "markets": markets_count,
            "events_with_full_odds": events_with_full_odds,
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
                "sportybet": {new: N, updated: N, snapshots: N, markets: N,
                              events_with_full_odds: N, error: None},
                "bet9ja": {new: N, updated: N, snapshots: N, markets: N,
                           events_with_full_odds: N, error: None},
            }
        """
        log.info("Starting competitor event scraping for all platforms")

        results: dict = {
            "sportybet": {
                "new": 0,
                "updated": 0,
                "snapshots": 0,
                "markets": 0,
                "events_with_full_odds": 0,
                "error": None,
            },
            "bet9ja": {
                "new": 0,
                "updated": 0,
                "snapshots": 0,
                "markets": 0,
                "events_with_full_odds": 0,
                "error": None,
            },
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
