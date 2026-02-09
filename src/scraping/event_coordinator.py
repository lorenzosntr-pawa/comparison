"""Event-centric scraping coordinator.

This module implements the EventCoordinator class, the core orchestration
layer for cross-platform odds scraping. It coordinates all platforms
(BetPawa, SportyBet, Bet9ja) in a unified, event-centric workflow.

Architecture Overview:
    1. Discovery: Parallel discovery from all platforms (discover_events)
    2. Queue: Build priority queue by kickoff urgency + coverage (build_priority_queue)
    3. Scrape: Process batches with per-event parallel platform requests (scrape_batch)
    4. Store: Persist results with dual-path (async queue vs sync) (store_batch_results)

Key Features:
    - from_settings() factory: Creates coordinator from DB Settings model
    - scrape_batch() async generator: Yields progress events for SSE streaming
    - store_batch_results() dual-path: Uses AsyncWriteQueue if available,
      falls back to synchronous flush+commit otherwise
    - Change detection: Only writes snapshots when odds actually changed
    - OddsCache integration: Updates in-memory cache immediately after scrape

Concurrency Model:
    - Per-platform semaphores control HTTP request parallelism
    - Event-level semaphore limits concurrent events per batch
    - Bet9ja gets 25ms delay after each request (rate limit sensitive)
    - Default limits: BetPawa=50, SportyBet=50, Bet9ja=15 concurrent requests

Usage:
    coordinator = EventCoordinator.from_settings(
        betpawa_client, sportybet_client, bet9ja_client, settings,
        odds_cache=cache, write_queue=queue
    )
    async for progress in coordinator.run_full_cycle(db, scrape_run_id):
        await broadcaster.publish(progress)
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.bookmaker import Bookmaker
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
    CompetitorSource,
    CompetitorTournament,
)
from src.db.models.event import Event, EventBookmaker
from src.db.models.event_scrape_status import EventScrapeStatus
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.db.models.sport import Sport, Tournament
from src.market_mapping.mappers.bet9ja import map_bet9ja_odds_to_betpawa
from src.market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from src.market_mapping.types.errors import MappingError
from src.market_mapping.types.sportybet import SportybetMarket
from src.scraping.schemas.coordinator import EventTarget, ScrapeBatch, ScrapeStatus

if TYPE_CHECKING:
    from src.caching.odds_cache import OddsCache
    from src.db.models.settings import Settings
    from src.scraping.clients.bet9ja import Bet9jaClient
    from src.scraping.clients.betpawa import BetPawaClient
    from src.scraping.clients.sportybet import SportyBetClient
    from src.storage.write_queue import AsyncWriteQueue

logger = structlog.get_logger(__name__)

# Default platform concurrency limits (from Phase 36 rate limit investigation)
# Use instance attributes for actual limits - use from_settings() for configurable values
DEFAULT_PLATFORM_CONCURRENCY = {
    "betpawa": 50,
    "sportybet": 50,
    "bet9ja": 15,
}
DEFAULT_BET9JA_DELAY_MS = 25  # 25ms delay after each Bet9ja request
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_CONCURRENT_EVENTS = 10  # Phase 56: concurrent events per batch


class EventCoordinator:
    """Coordinates event-centric scraping across all bookmakers.

    Flow:
    1. Parallel discovery from all platforms -> unified SR ID list
    2. Build priority queue based on kickoff + coverage
    3. Process batches: for each event, scrape all platforms in parallel (Phase 38)
    4. Store results with per-event status tracking (Phase 39)

    Attributes:
        _clients: Dict mapping platform names to their API clients.
        _batch_size: Number of events to include in each batch.
        _event_map: Unified map of SR ID -> EventTarget.
        _priority_queue: Sorted list of events by priority.
    """

    def __init__(
        self,
        betpawa_client: BetPawaClient,
        sportybet_client: SportyBetClient,
        bet9ja_client: Bet9jaClient,
        batch_size: int = DEFAULT_BATCH_SIZE,
        platform_concurrency: dict[str, int] | None = None,
        bet9ja_delay_ms: int = DEFAULT_BET9JA_DELAY_MS,
        odds_cache: OddsCache | None = None,
        write_queue: AsyncWriteQueue | None = None,
        max_concurrent_events: int = DEFAULT_MAX_CONCURRENT_EVENTS,
    ) -> None:
        """Initialize the EventCoordinator.

        Args:
            betpawa_client: BetPawa API client.
            sportybet_client: SportyBet API client.
            bet9ja_client: Bet9ja API client.
            batch_size: Number of events per batch (default 50).
            platform_concurrency: Dict of platform -> max concurrent requests.
                Defaults to {betpawa: 50, sportybet: 50, bet9ja: 15}.
            bet9ja_delay_ms: Delay in ms after each Bet9ja request (default 25).
            odds_cache: Optional in-memory OddsCache to populate after storage.
            write_queue: Optional AsyncWriteQueue for background DB writes.
                When provided, snapshot persistence is decoupled from scraping.
                When None, falls back to synchronous flush+commit.
            max_concurrent_events: Max events scraped in parallel per batch (default 10).
                With 3 platforms each, 10 events means up to 30 concurrent HTTP requests.
        """
        self._clients: dict[str, BetPawaClient | SportyBetClient | Bet9jaClient] = {
            "betpawa": betpawa_client,
            "sportybet": sportybet_client,
            "bet9ja": bet9ja_client,
        }
        self._batch_size = batch_size
        self._platform_concurrency = platform_concurrency or DEFAULT_PLATFORM_CONCURRENCY.copy()
        self._bet9ja_delay_ms = bet9ja_delay_ms
        self._odds_cache: OddsCache | None = odds_cache
        self._write_queue: AsyncWriteQueue | None = write_queue
        self._max_concurrent_events = max_concurrent_events
        self._event_map: dict[str, EventTarget] = {}
        self._priority_queue: list[EventTarget] = []
        self._last_discovery_timings: dict[str, int] = {}
        self._last_storage_timings: dict[str, int] = {}

    @classmethod
    def from_settings(
        cls,
        betpawa_client: BetPawaClient,
        sportybet_client: SportyBetClient,
        bet9ja_client: Bet9jaClient,
        settings: Settings,
        odds_cache: OddsCache | None = None,
        write_queue: AsyncWriteQueue | None = None,
    ) -> EventCoordinator:
        """Create EventCoordinator with tuning parameters from Settings model.

        Args:
            betpawa_client: BetPawa API client.
            sportybet_client: SportyBet API client.
            bet9ja_client: Bet9ja API client.
            settings: Settings model with tuning parameters.
            odds_cache: Optional in-memory OddsCache to populate after storage.
            write_queue: Optional AsyncWriteQueue for background DB writes.

        Returns:
            Configured EventCoordinator instance.
        """
        return cls(
            betpawa_client=betpawa_client,
            sportybet_client=sportybet_client,
            bet9ja_client=bet9ja_client,
            batch_size=settings.batch_size,
            platform_concurrency={
                "betpawa": settings.betpawa_concurrency,
                "sportybet": settings.sportybet_concurrency,
                "bet9ja": settings.bet9ja_concurrency,
            },
            bet9ja_delay_ms=settings.bet9ja_delay_ms,
            odds_cache=odds_cache,
            write_queue=write_queue,
            max_concurrent_events=getattr(
                settings, "max_concurrent_events", DEFAULT_MAX_CONCURRENT_EVENTS
            ),
        )

    # =========================================================================
    # DISCOVERY: Phase 1 - Parallel event discovery from all platforms
    # =========================================================================

    async def discover_events(self) -> dict[str, EventTarget]:
        """Discover events from all platforms in parallel.

        Runs discovery for BetPawa, SportyBet, and Bet9ja simultaneously,
        then merges results into a unified event map keyed by SR ID.

        Returns:
            Dict mapping SR ID to EventTarget with platform availability.
        """
        logger.info("Starting parallel event discovery")

        # Timed discovery wrappers for per-platform timing
        platform_timings_ms: dict[str, int] = {}

        async def _timed_discover(name: str, coro):
            t0 = time.perf_counter()
            result = await coro
            platform_timings_ms[name] = int((time.perf_counter() - t0) * 1000)
            return result

        # Run discovery in parallel with per-platform timing
        discovery_wall_start = time.perf_counter()
        results = await asyncio.gather(
            _timed_discover("betpawa", self._discover_betpawa()),
            _timed_discover("sportybet", self._discover_sportybet()),
            _timed_discover("bet9ja", self._discover_bet9ja()),
            return_exceptions=True,
        )
        discovery_total_ms = int((time.perf_counter() - discovery_wall_start) * 1000)

        # Merge into unified event map
        platforms = ["betpawa", "sportybet", "bet9ja"]
        discovery_counts: dict[str, int] = {}

        for platform, events_result in zip(platforms, results):
            if isinstance(events_result, Exception):
                logger.error(
                    "Platform discovery failed",
                    platform=platform,
                    error=str(events_result),
                )
                discovery_counts[platform] = 0
                continue

            events = events_result
            discovery_counts[platform] = len(events)

            for event in events:
                sr_id = event["sr_id"]
                kickoff = event["kickoff"]
                platform_id = event.get("platform_id", "")

                if sr_id in self._event_map:
                    # Event already discovered from another platform - add this platform
                    self._event_map[sr_id].platforms.add(platform)
                    # Store platform-specific ID for API calls
                    if platform_id:
                        self._event_map[sr_id].platform_ids[platform] = platform_id
                else:
                    # New event - create EventTarget
                    self._event_map[sr_id] = EventTarget(
                        sr_id=sr_id,
                        kickoff=kickoff,
                        platforms={platform},
                        platform_ids={platform: platform_id} if platform_id else {},
                        status=ScrapeStatus.PENDING,
                    )

        # Store discovery timing for progress events
        self._last_discovery_timings = {
            "betpawa_discovery_ms": platform_timings_ms.get("betpawa", 0),
            "sportybet_discovery_ms": platform_timings_ms.get("sportybet", 0),
            "bet9ja_discovery_ms": platform_timings_ms.get("bet9ja", 0),
            "discovery_total_ms": discovery_total_ms,
        }

        logger.info(
            "Event discovery complete",
            betpawa=discovery_counts.get("betpawa", 0),
            sportybet=discovery_counts.get("sportybet", 0),
            bet9ja=discovery_counts.get("bet9ja", 0),
            merged=len(self._event_map),
            **self._last_discovery_timings,
        )

        return self._event_map

    async def _discover_betpawa(self) -> list[dict]:
        """Discover events from BetPawa.

        Fetches all football competitions, then fetches events from each.
        Extracts SR IDs from the SPORTRADAR widget in each event.

        Returns:
            List of dicts with {sr_id, kickoff} for each upcoming event.
        """
        logger.info("Discovering BetPawa events")
        events: list[dict] = []
        now = datetime.now(timezone.utc)

        try:
            client = self._clients["betpawa"]
            # Fetch competition list
            categories_data = await client.fetch_categories()

            # Log response structure for debugging
            response_keys = list(categories_data.keys()) if isinstance(categories_data, dict) else []
            logger.info(
                "BetPawa categories response",
                response_keys=response_keys,
            )

            # Extract competition IDs from the nested structure
            # API structure: withRegions[0].regions[i].competitions[j].competition.id
            competition_ids: list[str] = []
            with_regions = categories_data.get("withRegions", [])
            regions = with_regions[0].get("regions", []) if with_regions else []

            logger.info(
                "BetPawa regions",
                regions_count=len(regions),
            )

            for region in regions:
                competitions = region.get("competitions", [])
                for comp in competitions:
                    # Competition ID is nested inside "competition" key
                    competition_data = comp.get("competition", {})
                    comp_id = str(competition_data.get("id", ""))
                    if comp_id:
                        competition_ids.append(comp_id)

            logger.info(
                "Found BetPawa competitions",
                count=len(competition_ids),
            )

            # Fetch events from each competition with semaphore
            semaphore = asyncio.Semaphore(5)

            async def fetch_comp_events(comp_id: str) -> list[dict]:
                async with semaphore:
                    try:
                        data = await client.fetch_events(comp_id)

                        # Parse events from response using correct structure
                        # API structure: responses[0].responses[] (not eventLists[].events[])
                        responses = data.get("responses", [])
                        if not responses:
                            logger.debug(
                                "BetPawa events response empty",
                                competition_id=comp_id,
                                response_keys=list(data.keys()),
                            )
                            return []

                        first_response = responses[0]
                        events_data = first_response.get("responses", [])

                        logger.debug(
                            "BetPawa events response structure",
                            competition_id=comp_id,
                            responses_count=len(responses),
                            events_count=len(events_data),
                        )

                        # Collect events from list response
                        # Try to get SR ID from list response first (old working pattern)
                        # Only queue for full fetch if SR ID not in list response
                        events_from_list: list[dict] = []
                        betpawa_event_ids: list[tuple[str, datetime]] = []

                        for event_data in events_data:
                            event_id = str(event_data.get("id", ""))
                            start_time = event_data.get("startTime")
                            if not event_id or not start_time:
                                continue

                            try:
                                kickoff = datetime.fromisoformat(
                                    start_time.replace("Z", "+00:00")
                                )
                                if kickoff <= now:  # Skip started events
                                    continue
                            except (ValueError, TypeError):
                                continue

                            # Try to get SR ID from list response widgets
                            # BetPawa's widget.id IS the SportRadar ID (8-digit numeric)
                            widgets = event_data.get("widgets", [])
                            sr_id = None
                            for widget in widgets:
                                if widget.get("type") == "SPORTRADAR":
                                    sr_id = widget.get("id")
                                    if sr_id:
                                        sr_id = str(sr_id)
                                    break

                            if sr_id:
                                # Got SR ID from list response - no need for full fetch
                                events_from_list.append({
                                    "sr_id": sr_id,
                                    "kickoff": kickoff,
                                    "platform_id": event_id,
                                })
                            else:
                                # No SR ID in list - queue for full fetch
                                betpawa_event_ids.append((event_id, kickoff))

                        if not events_from_list and not betpawa_event_ids:
                            return []

                        logger.debug(
                            "BetPawa competition events parsed",
                            competition_id=comp_id,
                            from_list=len(events_from_list),
                            need_full_fetch=len(betpawa_event_ids),
                        )

                        # Fetch full event details (with SR ID in widgets array)
                        # Uses nested semaphore for concurrency control
                        event_semaphore = asyncio.Semaphore(10)

                        async def fetch_full_event(
                            event_id: str, kickoff: datetime
                        ) -> dict | None:
                            async with event_semaphore:
                                try:
                                    full_data = await client.fetch_event(event_id)
                                    # Extract SR ID from widgets array
                                    # BetPawa's widget.id IS the SportRadar ID (8-digit numeric)
                                    widgets = full_data.get("widgets", [])
                                    sr_id = None
                                    for widget in widgets:
                                        if widget.get("type") == "SPORTRADAR":
                                            sr_id = widget.get("id")
                                            if sr_id:
                                                sr_id = str(sr_id)
                                            break

                                    if sr_id:
                                        return {
                                            "sr_id": sr_id,
                                            "kickoff": kickoff,
                                            "platform_id": event_id,
                                        }
                                except Exception as e:
                                    logger.debug(
                                        "Failed to fetch BetPawa event",
                                        event_id=event_id,
                                        error=str(e),
                                    )
                                return None

                        # Fetch full events only for those without SR ID in list
                        events_from_full: list[dict] = []
                        if betpawa_event_ids:
                            results = await asyncio.gather(
                                *[
                                    fetch_full_event(eid, ko)
                                    for eid, ko in betpawa_event_ids
                                ],
                                return_exceptions=True,
                            )

                            events_from_full = [
                                r
                                for r in results
                                if r is not None and not isinstance(r, Exception)
                            ]

                        # Combine events from list and full fetch
                        all_events = events_from_list + events_from_full

                        if events_from_list or events_from_full:
                            logger.debug(
                                "BetPawa competition events collected",
                                competition_id=comp_id,
                                from_list=len(events_from_list),
                                from_full_fetch=len(events_from_full),
                                total=len(all_events),
                            )

                        return all_events

                    except Exception as e:
                        logger.debug(
                            "Failed to fetch BetPawa competition",
                            competition_id=comp_id,
                            error=str(e),
                        )
                        return []

            results = await asyncio.gather(
                *[fetch_comp_events(c) for c in competition_ids],
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, list):
                    events.extend(result)

            logger.info("Discovered BetPawa events", count=len(events))

        except Exception as e:
            logger.error("BetPawa discovery failed", error=str(e))
            return []

        return events

    # BetPawa discovery flow:
    # 1. fetch_categories() -> competition IDs
    # 2. fetch_events(comp_id) -> BetPawa event IDs (list response, no widgets)
    # 3. fetch_event(event_id) -> full event with widgets array (contains SR ID)
    # Note: SR ID extraction is done inline in fetch_full_event() within _discover_betpawa()

    async def _discover_sportybet(self) -> list[dict]:
        """Discover events from SportyBet.

        Fetches tournament hierarchy, then fetches events from each tournament.
        Uses the eventId field which contains the SR ID.

        Returns:
            List of dicts with {sr_id, kickoff} for each upcoming event.
        """
        logger.debug("Discovering SportyBet events")
        events: list[dict] = []
        now = datetime.now(timezone.utc)

        try:
            client = self._clients["sportybet"]
            # Fetch tournament structure
            data = await client.fetch_tournaments()

            # Extract tournament IDs
            tournament_ids: list[str] = []
            sport_list = data.get("data", {}).get("sportList", [])
            for sport in sport_list:
                if sport.get("id") != "sr:sport:1":  # Football only
                    continue
                for category in sport.get("categories", []):
                    for tournament in category.get("tournaments", []):
                        t_id = tournament.get("id", "")
                        if t_id:
                            tournament_ids.append(t_id)

            logger.debug(
                "Found SportyBet tournaments",
                count=len(tournament_ids),
            )

            # Fetch events from each tournament with semaphore
            semaphore = asyncio.Semaphore(10)

            async def fetch_tournament_events(t_id: str) -> list[dict]:
                async with semaphore:
                    try:
                        event_list = await client.fetch_events_by_tournament(t_id)
                        parsed_events: list[dict] = []
                        for event_data in event_list:
                            parsed = self._parse_sportybet_event(event_data, now)
                            if parsed:
                                parsed_events.append(parsed)
                        return parsed_events
                    except Exception as e:
                        logger.debug(
                            "Failed to fetch SportyBet tournament",
                            tournament_id=t_id,
                            error=str(e),
                        )
                        return []

            results = await asyncio.gather(
                *[fetch_tournament_events(t) for t in tournament_ids],
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, list):
                    events.extend(result)

            logger.debug("Discovered SportyBet events", count=len(events))

        except Exception as e:
            logger.error("SportyBet discovery failed", error=str(e))
            return []

        return events

    def _parse_sportybet_event(
        self,
        event_data: dict,
        now: datetime,
    ) -> dict | None:
        """Parse a SportyBet event and extract SR ID and platform ID.

        Args:
            event_data: Raw event data from SportyBet API.
            now: Current UTC time for filtering started events.

        Returns:
            Dict with {sr_id, kickoff, platform_id} or None if not parseable/started.
        """
        # Extract SR ID from eventId (format: "sr:match:12345678")
        # The eventId IS the platform ID for SportyBet API calls
        event_id = event_data.get("eventId", "")
        if not event_id.startswith("sr:match:"):
            return None

        # Platform ID is the full format (sr:match:12345678)
        platform_id = event_id

        # SR ID is just the numeric part for cross-platform matching
        sr_id = event_id.replace("sr:match:", "")
        if not sr_id:
            return None

        # Parse kickoff time (estimateStartTime is Unix timestamp in ms)
        estimate_start = event_data.get("estimateStartTime")
        if not estimate_start:
            return None

        try:
            kickoff = datetime.fromtimestamp(estimate_start / 1000, tz=timezone.utc)
        except (ValueError, TypeError):
            return None

        # Filter out started events
        if kickoff <= now:
            return None

        return {"sr_id": sr_id, "kickoff": kickoff, "platform_id": platform_id}

    async def _discover_bet9ja(self) -> list[dict]:
        """Discover events from Bet9ja.

        Fetches sports/tournament hierarchy, then fetches events from each group.
        Uses the EXTID field which contains the SR ID.

        Returns:
            List of dicts with {sr_id, kickoff} for each upcoming event.
        """
        logger.debug("Discovering Bet9ja events")
        events: list[dict] = []
        now = datetime.now(timezone.utc)

        try:
            client = self._clients["bet9ja"]
            # Fetch sports structure
            data = await client.fetch_sports()

            # Extract group IDs (tournament IDs) from Soccer
            group_ids: list[str] = []
            soccer = data.get("D", {}).get("PAL", {}).get("1", {})
            sport_groups = soccer.get("SG", {})

            for sg_id, sg_data in sport_groups.items():
                groups = sg_data.get("G", {})
                for g_id in groups.keys():
                    group_ids.append(g_id)

            logger.debug(
                "Found Bet9ja groups",
                count=len(group_ids),
            )

            # Fetch events from each group with semaphore and delay
            semaphore = asyncio.Semaphore(15)

            async def fetch_group_events(g_id: str) -> list[dict]:
                async with semaphore:
                    try:
                        event_list = await client.fetch_events(g_id)
                        # Add delay to avoid rate limiting
                        await asyncio.sleep(0.025)  # 25ms delay
                        parsed_events: list[dict] = []
                        for event_data in event_list:
                            parsed = self._parse_bet9ja_event(event_data, now)
                            if parsed:
                                parsed_events.append(parsed)
                        return parsed_events
                    except Exception as e:
                        logger.debug(
                            "Failed to fetch Bet9ja group",
                            group_id=g_id,
                            error=str(e),
                        )
                        return []

            results = await asyncio.gather(
                *[fetch_group_events(g) for g in group_ids],
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, list):
                    events.extend(result)

            logger.debug("Discovered Bet9ja events", count=len(events))

        except Exception as e:
            logger.error("Bet9ja discovery failed", error=str(e))
            return []

        return events

    def _parse_bet9ja_event(
        self,
        event_data: dict,
        now: datetime,
    ) -> dict | None:
        """Parse a Bet9ja event and extract SR ID and platform ID.

        Args:
            event_data: Raw event data from Bet9ja API.
            now: Current UTC time for filtering started events.

        Returns:
            Dict with {sr_id, kickoff, platform_id} or None if not parseable/started.
        """
        # Extract SR ID from EXTID field (for cross-platform matching)
        sr_id = event_data.get("EXTID")
        if not sr_id:
            return None

        # Extract Bet9ja platform-specific event ID (for fetch_event API calls)
        # Use "ID" field, NOT "EXTID" - EXTID is the SR ID
        platform_id = str(event_data.get("ID", ""))
        if not platform_id:
            return None

        # Parse kickoff from STARTDATE (format: "YYYY-MM-DD HH:MM:SS")
        start_date_str = event_data.get("STARTDATE", "")
        try:
            # Bet9ja times are in UTC
            kickoff = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
            kickoff = kickoff.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

        # Filter out started events
        if kickoff <= now:
            return None

        return {"sr_id": sr_id, "kickoff": kickoff, "platform_id": platform_id}

    # =========================================================================
    # PRIORITY QUEUE: Phase 2 - Build queue and extract batches
    # =========================================================================

    def build_priority_queue(self) -> list[EventTarget]:
        """Build priority queue from discovered events.

        Sorts events by priority_key() which orders by:
        1. Urgency tier (imminent < 30min > soon < 2hr > future)
        2. Kickoff time (earlier = higher priority)
        3. Coverage count (more platforms = higher priority)
        4. BetPawa presence (has BetPawa = higher priority)

        Returns:
            Sorted list of EventTarget objects.
        """
        # Python heapq doesn't support key parameter directly,
        # so we sort by priority_key instead
        self._priority_queue = sorted(
            self._event_map.values(),
            key=lambda e: e.priority_key(),
        )

        logger.info(
            "Built priority queue",
            total_events=len(self._priority_queue),
            stats=self.get_queue_stats(),
        )

        return self._priority_queue

    def get_next_batch(self) -> ScrapeBatch | None:
        """Get the next batch of events to scrape.

        Pops up to batch_size events from the front of the priority queue.

        Returns:
            ScrapeBatch with events, or None if queue is empty.
        """
        if not self._priority_queue:
            return None

        # Pop batch_size events from front of queue
        batch_count = min(self._batch_size, len(self._priority_queue))
        batch_events = self._priority_queue[:batch_count]
        self._priority_queue = self._priority_queue[batch_count:]

        batch_id = f"batch_{uuid.uuid4().hex[:8]}"

        logger.debug(
            "Created batch",
            batch_id=batch_id,
            event_count=len(batch_events),
            remaining=len(self._priority_queue),
        )

        return ScrapeBatch(
            batch_id=batch_id,
            events=batch_events,
            created_at=datetime.now(timezone.utc),
        )

    def has_pending_events(self) -> bool:
        """Check if there are events remaining in the queue.

        Returns:
            True if queue has events, False otherwise.
        """
        return bool(self._priority_queue)

    def get_queue_stats(self) -> dict:
        """Get statistics about the priority queue.

        Returns:
            Dict with total_events, events_by_urgency, events_by_coverage.
        """
        if not self._event_map:
            return {
                "total_events": 0,
                "events_by_urgency": {"imminent": 0, "soon": 0, "future": 0},
                "events_by_coverage": {"3_platforms": 0, "2_platforms": 0, "1_platform": 0},
            }

        now = datetime.now(timezone.utc)
        urgency_counts = {"imminent": 0, "soon": 0, "future": 0}
        coverage_counts = {"3_platforms": 0, "2_platforms": 0, "1_platform": 0}

        for event in self._event_map.values():
            # Handle both tz-aware and naive datetimes
            kickoff_utc = event.kickoff
            if kickoff_utc.tzinfo is None:
                kickoff_utc = kickoff_utc.replace(tzinfo=timezone.utc)

            minutes_until = (kickoff_utc - now).total_seconds() / 60

            if minutes_until < 30:
                urgency_counts["imminent"] += 1
            elif minutes_until < 120:
                urgency_counts["soon"] += 1
            else:
                urgency_counts["future"] += 1

            coverage = event.coverage_count
            if coverage >= 3:
                coverage_counts["3_platforms"] += 1
            elif coverage == 2:
                coverage_counts["2_platforms"] += 1
            else:
                coverage_counts["1_platform"] += 1

        return {
            "total_events": len(self._event_map),
            "events_by_urgency": urgency_counts,
            "events_by_coverage": coverage_counts,
        }

    def get_event_map(self) -> dict[str, EventTarget]:
        """Get the current event map.

        Returns:
            Dict mapping SR ID to EventTarget.
        """
        return self._event_map

    def clear(self) -> None:
        """Clear all discovered events and the priority queue.

        Call this to reset the coordinator for a new discovery cycle.
        """
        self._event_map.clear()
        self._priority_queue.clear()
        logger.debug("Coordinator cleared")

    # =========================================================================
    # BATCH SCRAPING: Phase 3 - Parallel platform scraping per event
    # =========================================================================

    async def _scrape_event_all_platforms(
        self,
        event: EventTarget,
        semaphores: dict[str, asyncio.Semaphore],
    ) -> dict:
        """Scrape single event from all available platforms in parallel.

        For each platform in event.platforms, fetch odds using the platform-specific
        event ID. Uses semaphores for concurrency control and adds delay for Bet9ja.

        Args:
            event: EventTarget with platforms and platform_ids populated.
            semaphores: Dict of platform -> Semaphore for concurrency control.

        Returns:
            Dict with keys: data (platform->result), errors (platform->error_str), timing_ms
        """
        start_time = time.perf_counter()
        data: dict[str, dict] = {}
        errors: dict[str, str] = {}

        platform_timings: dict[str, int] = {}

        async def scrape_platform(platform: str) -> tuple[str, dict | None, str | None]:
            """Scrape a single platform for this event."""
            # Check if we have the platform ID
            platform_id = event.platform_ids.get(platform)
            if not platform_id:
                return (platform, None, "No platform ID available")

            try:
                async with semaphores[platform]:
                    platform_start = time.perf_counter()
                    client = self._clients[platform]
                    result = await client.fetch_event(platform_id)

                    # Add delay for Bet9ja to avoid rate limiting
                    if platform == "bet9ja":
                        await asyncio.sleep(self._bet9ja_delay_ms / 1000)

                    platform_timings[platform] = int(
                        (time.perf_counter() - platform_start) * 1000
                    )
                    return (platform, result, None)
            except Exception as e:
                logger.debug(
                    "Platform scrape failed",
                    platform=platform,
                    sr_id=event.sr_id,
                    platform_id=platform_id,
                    error=str(e),
                )
                return (platform, None, str(e))

        # Scrape all platforms in parallel
        tasks = [scrape_platform(p) for p in event.platforms]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                # This shouldn't happen since we catch exceptions in scrape_platform
                logger.error("Unexpected exception in scrape_platform", error=str(result))
                continue

            platform, platform_data, error = result
            if platform_data is not None:
                data[platform] = platform_data
            if error is not None:
                errors[platform] = error

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return {
            "data": data,
            "errors": errors,
            "timing_ms": elapsed_ms,
            "platform_timings": platform_timings,
        }

    async def scrape_batch(
        self,
        batch: ScrapeBatch,
    ) -> list[dict]:
        """Scrape all events in batch concurrently, returning progress list.

        Processes events concurrently up to max_concurrent_events limit.
        For each event, scrapes all platforms in parallel (using per-platform
        semaphores to throttle load), updates event status and results,
        and collects progress events for SSE streaming.

        Args:
            batch: ScrapeBatch containing events to scrape.

        Returns:
            List of progress dicts with event_type, sr_id, and platform results.
        """
        # Create semaphores for all platforms (reuse across batch)
        semaphores = {
            platform: asyncio.Semaphore(limit)
            for platform, limit in self._platform_concurrency.items()
        }

        # Event-level concurrency semaphore (Phase 56)
        event_semaphore = asyncio.Semaphore(self._max_concurrent_events)

        logger.debug(
            "Starting batch scrape",
            batch_id=batch["batch_id"],
            event_count=len(batch["events"]),
            max_concurrent_events=self._max_concurrent_events,
        )

        async def _scrape_single_event(event: EventTarget) -> list[dict]:
            """Scrape a single event with concurrency control.

            Acquires the event semaphore, scrapes all platforms for this event,
            and returns progress dicts (start + complete).
            """
            progress: list[dict] = []

            async with event_semaphore:
                # Mark event as in progress
                event.status = ScrapeStatus.IN_PROGRESS

                # Collect "scraping started" progress event
                progress.append({
                    "event_type": "EVENT_SCRAPING",
                    "sr_id": event.sr_id,
                    "platforms_pending": list(event.platforms),
                })

                # Scrape all platforms in parallel (per-platform semaphores throttle load)
                result = await self._scrape_event_all_platforms(event, semaphores)

                # Update event with results
                event.results = result["data"]
                event.errors = result["errors"]

                # Determine final status
                if result["errors"]:
                    if result["data"]:
                        event.status = ScrapeStatus.COMPLETED
                    else:
                        event.status = ScrapeStatus.FAILED
                else:
                    event.status = ScrapeStatus.COMPLETED

                # Collect "scraping complete" progress event
                progress.append({
                    "event_type": "EVENT_SCRAPED",
                    "sr_id": event.sr_id,
                    "platforms_scraped": list(result["data"].keys()),
                    "platforms_failed": list(result["errors"].keys()),
                    "timing_ms": result["timing_ms"],
                    "platform_timings": result.get("platform_timings", {}),
                })

            return progress

        # Fire off all events concurrently (semaphore limits actual parallelism)
        results = await asyncio.gather(
            *[_scrape_single_event(event) for event in batch["events"]],
            return_exceptions=True,
        )

        # Flatten results into a single list of progress dicts
        all_progress: list[dict] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    "Event scrape task failed",
                    batch_id=batch["batch_id"],
                    error=str(result),
                )
                continue
            all_progress.extend(result)

        logger.debug(
            "Batch scrape complete",
            batch_id=batch["batch_id"],
            concurrent_limit=self._max_concurrent_events,
        )

        return all_progress

    # =========================================================================
    # STORAGE: Phase 4 - Store scraped results in database
    # =========================================================================

    async def store_batch_results(
        self,
        db: AsyncSession,
        batch: ScrapeBatch,
        scrape_run_id: int,
    ) -> dict:
        """Store scraped batch results in database using bulk insert pattern.

        Processes events from batch, creates EventScrapeStatus records for tracking,
        and stores odds data to appropriate tables based on platform:
        - BetPawa -> OddsSnapshot + MarketOdds
        - SportyBet/Bet9ja -> CompetitorOddsSnapshot + CompetitorMarketOdds

        Args:
            db: AsyncSession for database operations.
            batch: ScrapeBatch containing events with results populated.
            scrape_run_id: FK to scrape_runs.id for tracking.

        Returns:
            Dict with {events_stored, snapshots_created, errors}.
        """
        logger.debug(
            "Storing batch results",
            batch_id=batch["batch_id"],
            event_count=len(batch["events"]),
        )

        # Counters for summary
        events_stored = 0
        snapshots_created = 0
        errors = 0

        # Storage sub-phase timing
        storage_lookups_start = time.perf_counter()

        # Pre-fetch bookmaker IDs
        bookmaker_ids = await self._get_bookmaker_ids(db)

        # Pre-fetch event mappings (SR ID -> DB event ID)
        sr_ids = [event.sr_id for event in batch["events"]]
        event_id_map = await self._get_event_ids_by_sr_ids(db, sr_ids)

        # Pre-fetch competitor event mappings (SR ID -> CompetitorEvent ID by source)
        competitor_event_map = await self._get_competitor_event_ids_by_sr_ids(db, sr_ids)

        # Get/create fallback tournaments for events discovered during scraping
        sport_id = await self._get_or_create_fallback_sport(db)
        fallback_tournament_id = await self._get_or_create_fallback_tournament(db, sport_id)
        fallback_competitor_tournament_ids = {
            CompetitorSource.SPORTYBET: await self._get_or_create_fallback_competitor_tournament(
                db, CompetitorSource.SPORTYBET, sport_id
            ),
            CompetitorSource.BET9JA: await self._get_or_create_fallback_competitor_tournament(
                db, CompetitorSource.BET9JA, sport_id
            ),
        }

        storage_lookups_ms = int((time.perf_counter() - storage_lookups_start) * 1000)

        # Collect all records for bulk operations
        storage_processing_start = time.perf_counter()
        status_records: list[EventScrapeStatus] = []

        # Collect parsed market data alongside metadata for both paths (sync and async)
        # Each entry: (event_id, bookmaker_id, raw_data, parsed_markets_orm)
        bp_parsed: list[tuple[int, int, dict | None, list[MarketOdds]]] = []
        # Each entry: (competitor_event_id, sr_id, source_value, raw_data, parsed_markets_orm)
        comp_parsed: list[tuple[int, str, str, dict | None, list[CompetitorMarketOdds]]] = []

        # Process each event in batch
        for event in batch["events"]:
            # Skip events that completely failed (no data at all)
            if event.status == ScrapeStatus.FAILED and not event.results:
                # Create EventScrapeStatus for failed event
                status_record = EventScrapeStatus(
                    scrape_run_id=scrape_run_id,
                    sportradar_id=event.sr_id,
                    status="failed",
                    platforms_requested=list(event.platforms),
                    platforms_scraped=[],
                    platforms_failed=list(event.errors.keys()) if event.errors else list(event.platforms),
                    timing_ms=0,
                    error_details=event.errors if event.errors else None,
                )
                status_records.append(status_record)
                errors += 1
                continue

            # Calculate timing from event result (stored during scrape)
            timing_ms = 0
            if event.results:
                # Timing is tracked per-event during scrape_batch
                # For now, estimate from available data
                timing_ms = 0  # Will be updated when we have timing data

            # Create EventScrapeStatus record
            status_record = EventScrapeStatus(
                scrape_run_id=scrape_run_id,
                sportradar_id=event.sr_id,
                status="completed" if event.status == ScrapeStatus.COMPLETED else "failed",
                platforms_requested=list(event.platforms),
                platforms_scraped=list(event.results.keys()),
                platforms_failed=list(event.errors.keys()) if event.errors else [],
                timing_ms=timing_ms,
                error_details=event.errors if event.errors else None,
            )
            status_records.append(status_record)

            # Process platform results
            for platform, raw_data in event.results.items():
                if raw_data is None:
                    continue

                try:
                    if platform == "betpawa":
                        # BetPawa -> OddsSnapshot + MarketOdds
                        bookmaker_id = bookmaker_ids.get("betpawa")
                        if bookmaker_id is None:
                            continue

                        event_id = event_id_map.get(event.sr_id)
                        if event_id is None:
                            # Create Event from raw data (FIX: v1.7 was skipping this)
                            # Get or create proper tournament from competition/region in raw_data
                            actual_tournament_id = await self._get_or_create_tournament_from_betpawa_raw(
                                db=db,
                                raw_data=raw_data,
                                sport_id=sport_id,
                            )
                            platform_id = event.platform_ids.get("betpawa", str(raw_data.get("id", "")))
                            event_id = await self._create_event_from_betpawa_raw(
                                db=db,
                                sr_id=event.sr_id,
                                raw_data=raw_data,
                                tournament_id=actual_tournament_id,
                                bookmaker_id=bookmaker_id,
                                platform_id=platform_id,
                            )
                            # Update map for any subsequent lookups
                            event_id_map[event.sr_id] = event_id

                        # Parse markets
                        markets = self._parse_betpawa_markets(raw_data)
                        bp_parsed.append((event_id, bookmaker_id, raw_data, markets))
                        snapshots_created += 1

                    else:
                        # SportyBet/Bet9ja -> CompetitorOddsSnapshot + CompetitorMarketOdds
                        source = CompetitorSource.SPORTYBET if platform == "sportybet" else CompetitorSource.BET9JA
                        competitor_event_id = competitor_event_map.get((event.sr_id, source.value))

                        if competitor_event_id is None:
                            # Create CompetitorEvent from raw data (FIX: v1.7 was skipping this)
                            platform_id = event.platform_ids.get(platform, "")
                            if not platform_id and source == CompetitorSource.BET9JA:
                                # Bet9ja uses ID field
                                platform_id = str(raw_data.get("ID", ""))

                            # Get or create proper tournament from raw data with country
                            competitor_tournament_id = await self._get_or_create_competitor_tournament_from_raw(
                                db=db,
                                source=source,
                                raw_data=raw_data,
                                sport_id=sport_id,
                            )

                            competitor_event_id = await self._create_competitor_event_from_raw(
                                db=db,
                                sr_id=event.sr_id,
                                source=source,
                                raw_data=raw_data,
                                tournament_id=competitor_tournament_id,
                                platform_id=platform_id,
                            )
                            # Update map for any subsequent lookups
                            competitor_event_map[(event.sr_id, source.value)] = competitor_event_id

                        # FIX: Also create EventBookmaker for this platform if BetPawa Event exists
                        # This enables min_bookmakers filter to work for cross-platform events
                        bp_event_id = event_id_map.get(event.sr_id)
                        if bp_event_id is not None:
                            bookmaker_id = bookmaker_ids.get(platform)
                            if bookmaker_id is not None:
                                # Get platform_id for EventBookmaker
                                platform_id = event.platform_ids.get(platform, "")
                                if not platform_id:
                                    if source == CompetitorSource.SPORTYBET:
                                        platform_id = raw_data.get("eventId", f"sr:match:{event.sr_id}")
                                    else:
                                        platform_id = str(raw_data.get("ID", ""))
                                # Create EventBookmaker if not exists
                                await self._ensure_event_bookmaker(
                                    db=db,
                                    event_id=bp_event_id,
                                    bookmaker_id=bookmaker_id,
                                    external_event_id=platform_id,
                                )

                        # Parse markets based on platform
                        if platform == "sportybet":
                            markets = self._parse_sportybet_markets(raw_data)
                        else:  # bet9ja
                            markets = self._parse_bet9ja_markets(raw_data)

                        comp_parsed.append((competitor_event_id, event.sr_id, source.value, raw_data, markets))
                        snapshots_created += 1

                except Exception as e:
                    logger.warning(
                        "Failed to process platform result",
                        sr_id=event.sr_id,
                        platform=platform,
                        error=str(e),
                    )
                    errors += 1

            events_stored += 1

        # Reconciliation pass: Link CompetitorEvents and create EventBookmaker links
        # This handles ordering edge case where competitor processed before BetPawa in same batch
        for sr_id, event_id in event_id_map.items():
            # Update any CompetitorEvents for this SR ID that have NULL betpawa_event_id
            await db.execute(
                update(CompetitorEvent)
                .where(
                    CompetitorEvent.sportradar_id == sr_id,
                    CompetitorEvent.betpawa_event_id.is_(None)
                )
                .values(betpawa_event_id=event_id)
            )

        # Create EventBookmaker links for competitors that have data for BetPawa events
        # This ensures the Odds Comparison API can find competitor bookmakers
        for (sr_id, source), comp_event_id in competitor_event_map.items():
            bp_event_id = event_id_map.get(sr_id)
            if bp_event_id is not None:
                platform = "sportybet" if source == CompetitorSource.SPORTYBET.value else "bet9ja"
                bookmaker_id = bookmaker_ids.get(platform)
                if bookmaker_id is not None:
                    # Get the CompetitorEvent to retrieve external_id
                    comp_event_result = await db.execute(
                        select(CompetitorEvent.external_id).where(CompetitorEvent.id == comp_event_id)
                    )
                    external_id = comp_event_result.scalar_one_or_none() or f"sr:{sr_id}"
                    await self._ensure_event_bookmaker(
                        db=db,
                        event_id=bp_event_id,
                        bookmaker_id=bookmaker_id,
                        external_event_id=external_id,
                    )

        storage_processing_ms = int((time.perf_counter() - storage_processing_start) * 1000)

        # Insert EventScrapeStatus records (no FK dependencies)
        for status_record in status_records:
            db.add(status_record)

        # -----------------------------------------------------------------
        # Branch: async write queue vs synchronous fallback
        # -----------------------------------------------------------------
        if self._write_queue is not None and self._odds_cache is not None:
            # ============================================================
            # ASYNC PATH: build DTOs, change detection, cache, enqueue
            # ============================================================
            from src.caching.change_detection import classify_batch_changes
            from src.caching.warmup import snapshot_to_cached_from_data
            from src.storage.write_queue import (
                CompetitorSnapshotWriteData,
                MarketWriteData,
                SnapshotWriteData,
                WriteBatch,
            )

            # 1. Build SnapshotWriteData DTOs from parsed results
            bp_write_data: list[SnapshotWriteData] = []
            # Track mapping: index in bp_write_data -> (event_id, bookmaker_id)
            bp_meta: list[tuple[int, int]] = []

            for event_id, bookmaker_id, raw_data, orm_markets in bp_parsed:
                market_dtos = tuple(
                    MarketWriteData(
                        betpawa_market_id=m.betpawa_market_id,
                        betpawa_market_name=m.betpawa_market_name,
                        line=m.line,
                        handicap_type=getattr(m, "handicap_type", None),
                        handicap_home=getattr(m, "handicap_home", None),
                        handicap_away=getattr(m, "handicap_away", None),
                        outcomes=m.outcomes if isinstance(m.outcomes, list) else [],
                        market_groups=getattr(m, "market_groups", None),
                    )
                    for m in orm_markets
                )
                swd = SnapshotWriteData(
                    event_id=event_id,
                    bookmaker_id=bookmaker_id,
                    scrape_run_id=scrape_run_id,
                    raw_response=raw_data,
                    markets=market_dtos,
                )
                bp_write_data.append(swd)
                bp_meta.append((event_id, bookmaker_id))

            comp_write_data: list[CompetitorSnapshotWriteData] = []
            # Track mapping: index in comp_write_data -> (sr_id, source_value, competitor_event_id)
            comp_meta: list[tuple[str, str, int]] = []

            for competitor_event_id, sr_id, source_value, raw_data, orm_markets in comp_parsed:
                market_dtos = tuple(
                    MarketWriteData(
                        betpawa_market_id=m.betpawa_market_id,
                        betpawa_market_name=m.betpawa_market_name,
                        line=m.line,
                        handicap_type=getattr(m, "handicap_type", None),
                        handicap_home=getattr(m, "handicap_home", None),
                        handicap_away=getattr(m, "handicap_away", None),
                        outcomes=m.outcomes if isinstance(m.outcomes, list) else [],
                        market_groups=getattr(m, "market_groups", None),
                    )
                    for m in orm_markets
                )
                cswd = CompetitorSnapshotWriteData(
                    competitor_event_id=competitor_event_id,
                    scrape_run_id=scrape_run_id,
                    raw_response=raw_data,
                    markets=market_dtos,
                )
                comp_write_data.append(cswd)
                comp_meta.append((sr_id, source_value, competitor_event_id))

            # 2. Run change detection
            change_detection_start = time.perf_counter()

            # Build tuples for classify_batch_changes:
            # betpawa: (event_id, bookmaker_id, markets_data_as_dicts)
            bp_for_cd: list[tuple[int, int, list]] = []
            for swd in bp_write_data:
                markets_as_dicts = [
                    {
                        "betpawa_market_id": m.betpawa_market_id,
                        "line": m.line,
                        "outcomes": m.outcomes if isinstance(m.outcomes, list) else [],
                    }
                    for m in swd.markets
                ]
                bp_for_cd.append((swd.event_id, swd.bookmaker_id, markets_as_dicts))

            # competitor: (event_id, source, markets_data_as_dicts)
            # Note: classify_batch_changes uses betpawa event_id for cache lookup
            comp_for_cd: list[tuple[int, str, list]] = []
            for idx, cswd in enumerate(comp_write_data):
                sr_id_val, source_value, _comp_eid = comp_meta[idx]
                betpawa_eid = event_id_map.get(sr_id_val, 0)
                markets_as_dicts = [
                    {
                        "betpawa_market_id": m.betpawa_market_id,
                        "line": m.line,
                        "outcomes": m.outcomes if isinstance(m.outcomes, list) else [],
                    }
                    for m in cswd.markets
                ]
                comp_for_cd.append((betpawa_eid, source_value, markets_as_dicts))

            changed_bp, changed_comp, unchanged_bp_ids, unchanged_comp_ids = classify_batch_changes(
                self._odds_cache, bp_for_cd, comp_for_cd
            )

            change_detection_ms = int((time.perf_counter() - change_detection_start) * 1000)

            logger.info(
                "change_detection.results",
                changed_bp=len(changed_bp),
                unchanged_bp=len(unchanged_bp_ids),
                changed_comp=len(changed_comp),
                unchanged_comp=len(unchanged_comp_ids),
            )

            # Build sets of changed keys for filtering DTOs to enqueue
            changed_bp_keys: set[tuple[int, int]] = {
                (eid, bk_id) for eid, bk_id, _mkt in changed_bp
            }
            changed_comp_keys: set[tuple[int, str]] = set()
            for betpawa_eid, source_val, _mkt in changed_comp:
                changed_comp_keys.add((betpawa_eid, source_val))

            # 3. Update cache immediately for ALL data (changed + unchanged)
            cache_update_start = time.perf_counter()
            cache_updated = 0
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

            # Build kickoff lookup from batch events: sr_id -> kickoff (naive UTC)
            kickoff_by_sr: dict[str, datetime] = {}
            for evt in batch["events"]:
                ko = evt.kickoff
                if ko.tzinfo is not None:
                    ko = ko.replace(tzinfo=None)
                kickoff_by_sr[evt.sr_id] = ko

            # Reverse map: event_id -> sr_id
            eid_to_sr: dict[int, str] = {v: k for k, v in event_id_map.items()}

            for idx, swd in enumerate(bp_write_data):
                try:
                    sr_id_val = eid_to_sr.get(swd.event_id)
                    kickoff = kickoff_by_sr.get(sr_id_val) if sr_id_val else None
                    is_changed = (swd.event_id, swd.bookmaker_id) in changed_bp_keys

                    # For unchanged snapshots, preserve existing snapshot_id from cache
                    if is_changed:
                        snap_id = 0  # Real ID assigned later by write handler
                    else:
                        existing = self._odds_cache.get_betpawa_snapshot(swd.event_id)
                        cached_snap = existing.get(swd.bookmaker_id) if existing else None
                        snap_id = cached_snap.snapshot_id if cached_snap else 0

                    cached = snapshot_to_cached_from_data(
                        snapshot_id=snap_id,
                        event_id=swd.event_id,
                        bookmaker_id=swd.bookmaker_id,
                        captured_at=now_naive,
                        last_confirmed_at=now_naive,
                        markets=swd.markets,
                    )
                    self._odds_cache.put_betpawa_snapshot(
                        event_id=swd.event_id,
                        bookmaker_id=swd.bookmaker_id,
                        snapshot=cached,
                        kickoff=kickoff,
                    )
                    cache_updated += 1
                except Exception as e:
                    logger.debug(
                        "Cache update failed for BetPawa snapshot",
                        event_id=swd.event_id,
                        error=str(e),
                    )

            for idx, cswd in enumerate(comp_write_data):
                try:
                    sr_id_val, source_value, _comp_eid = comp_meta[idx]
                    betpawa_eid = event_id_map.get(sr_id_val)
                    if not betpawa_eid:
                        continue
                    kickoff = kickoff_by_sr.get(sr_id_val)
                    is_changed = (betpawa_eid, source_value) in changed_comp_keys

                    if is_changed:
                        snap_id = 0
                    else:
                        existing = self._odds_cache.get_competitor_snapshot(betpawa_eid)
                        cached_snap = existing.get(source_value) if existing else None
                        snap_id = cached_snap.snapshot_id if cached_snap else 0

                    cached = snapshot_to_cached_from_data(
                        snapshot_id=snap_id,
                        event_id=betpawa_eid,
                        bookmaker_id=0,
                        captured_at=now_naive,
                        last_confirmed_at=now_naive,
                        markets=cswd.markets,
                    )
                    self._odds_cache.put_competitor_snapshot(
                        event_id=betpawa_eid,
                        source=source_value,
                        snapshot=cached,
                        kickoff=kickoff,
                    )
                    cache_updated += 1
                except Exception as e:
                    logger.debug(
                        "Cache update failed for competitor snapshot",
                        competitor_event_id=cswd.competitor_event_id,
                        error=str(e),
                    )

            cache_update_ms = int((time.perf_counter() - cache_update_start) * 1000)
            logger.debug(
                "Cache updated",
                snapshots=cache_updated,
                duration_ms=cache_update_ms,
            )

            # 4. Commit coordinator session (events, competitors, reconciliation, status — no snapshots)
            storage_commit_start = time.perf_counter()
            await db.commit()
            storage_commit_ms = int((time.perf_counter() - storage_commit_start) * 1000)

            # 5. Enqueue write batch (only changed data + unchanged IDs)
            queue_enqueue_start = time.perf_counter()

            # Filter DTOs to only include changed snapshots
            changed_bp_dtos = tuple(
                swd for swd in bp_write_data
                if (swd.event_id, swd.bookmaker_id) in changed_bp_keys
            )
            changed_comp_dtos = tuple(
                cswd for idx, cswd in enumerate(comp_write_data)
                if (event_id_map.get(comp_meta[idx][0], 0), comp_meta[idx][1]) in changed_comp_keys
            )

            write_batch = WriteBatch(
                changed_betpawa=changed_bp_dtos,
                changed_competitor=changed_comp_dtos,
                unchanged_betpawa_ids=tuple(unchanged_bp_ids),
                unchanged_competitor_ids=tuple(unchanged_comp_ids),
                scrape_run_id=scrape_run_id,
                batch_index=0,  # Will be set by caller if needed
            )
            await self._write_queue.enqueue(write_batch)

            queue_enqueue_ms = int((time.perf_counter() - queue_enqueue_start) * 1000)

            # Store timing breakdown for progress events
            self._last_storage_timings = {
                "storage_lookups_ms": storage_lookups_ms,
                "storage_processing_ms": storage_processing_ms,
                "storage_flush_ms": 0,  # No sync flush in async path
                "storage_commit_ms": storage_commit_ms,
                "cache_update_ms": cache_update_ms,
                "change_detection_ms": change_detection_ms,
                "queue_enqueue_ms": queue_enqueue_ms,
            }

        else:
            # ============================================================
            # SYNC FALLBACK: original bulk insert (when write_queue is None)
            # ============================================================
            betpawa_snapshots: list[tuple[OddsSnapshot, list[MarketOdds]]] = []
            competitor_snapshots: list[tuple[CompetitorOddsSnapshot, list[CompetitorMarketOdds]]] = []

            for event_id, bookmaker_id, raw_data, orm_markets in bp_parsed:
                snapshot = OddsSnapshot(
                    event_id=event_id,
                    bookmaker_id=bookmaker_id,
                    scrape_run_id=scrape_run_id,
                    raw_response=raw_data,
                )
                betpawa_snapshots.append((snapshot, orm_markets))

            for competitor_event_id, sr_id, source_value, raw_data, orm_markets in comp_parsed:
                snapshot = CompetitorOddsSnapshot(
                    competitor_event_id=competitor_event_id,
                    scrape_run_id=scrape_run_id,
                    raw_response=raw_data,
                )
                competitor_snapshots.append((snapshot, orm_markets))

            # Add all snapshots first (both BetPawa and competitor)
            for snapshot, _markets in betpawa_snapshots:
                db.add(snapshot)
            for snapshot, _markets in competitor_snapshots:
                db.add(snapshot)

            # Single flush to get all snapshot IDs at once
            storage_flush_start = time.perf_counter()
            await db.flush()
            storage_flush_ms = int((time.perf_counter() - storage_flush_start) * 1000)

            # Now add all markets with their snapshot IDs (IDs populated after flush)
            for snapshot, markets in betpawa_snapshots:
                for market in markets:
                    market.snapshot_id = snapshot.id
                    db.add(market)

            for snapshot, markets in competitor_snapshots:
                for market in markets:
                    market.snapshot_id = snapshot.id
                    db.add(market)

            # Commit all changes
            storage_commit_start = time.perf_counter()
            await db.commit()
            storage_commit_ms = int((time.perf_counter() - storage_commit_start) * 1000)

            # Update in-memory cache with freshly stored snapshots
            cache_update_ms = 0
            if self._odds_cache is not None:
                cache_update_start = time.perf_counter()
                cache_updated = 0

                # Build kickoff lookup from batch events: sr_id -> kickoff (naive UTC)
                kickoff_by_sr: dict[str, datetime] = {}
                for evt in batch["events"]:
                    ko = evt.kickoff
                    # Ensure naive UTC for cache storage consistency
                    if ko.tzinfo is not None:
                        ko = ko.replace(tzinfo=None)
                    kickoff_by_sr[evt.sr_id] = ko

                # Build reverse map: event_id -> sr_id for BetPawa lookups
                # (event_id_map is sr_id -> event_id)
                eid_to_sr: dict[int, str] = {v: k for k, v in event_id_map.items()}

                # Build reverse map: competitor_event_id -> (sr_id, source_value)
                comp_eid_to_sr: dict[int, tuple[str, str]] = {
                    v: k for k, v in competitor_event_map.items()
                }

                from src.caching.warmup import snapshot_to_cached_from_models

                # Populate cache from BetPawa snapshots
                for snapshot, markets in betpawa_snapshots:
                    try:
                        sr_id = eid_to_sr.get(snapshot.event_id)
                        kickoff = kickoff_by_sr.get(sr_id) if sr_id else None
                        # captured_at may be None if server_default not yet loaded
                        captured_at = snapshot.captured_at or datetime.now(timezone.utc).replace(tzinfo=None)
                        # Use last_confirmed_at for freshness (fallback to captured_at for old data)
                        last_confirmed = snapshot.last_confirmed_at or captured_at
                        cached = snapshot_to_cached_from_models(
                            snapshot_id=snapshot.id,
                            event_id=snapshot.event_id,
                            bookmaker_id=snapshot.bookmaker_id,
                            captured_at=captured_at,
                            last_confirmed_at=last_confirmed,
                            markets=markets,
                        )
                        self._odds_cache.put_betpawa_snapshot(
                            event_id=snapshot.event_id,
                            bookmaker_id=snapshot.bookmaker_id,
                            snapshot=cached,
                            kickoff=kickoff,
                        )
                        cache_updated += 1
                    except Exception as e:
                        logger.debug(
                            "Cache update failed for BetPawa snapshot",
                            event_id=snapshot.event_id,
                            error=str(e),
                        )

                # Populate cache from competitor snapshots
                for snapshot, markets in competitor_snapshots:
                    try:
                        comp_key = comp_eid_to_sr.get(snapshot.competitor_event_id)
                        if not comp_key:
                            continue
                        sr_id, source_value = comp_key
                        betpawa_event_id = event_id_map.get(sr_id)
                        if not betpawa_event_id:
                            continue
                        kickoff = kickoff_by_sr.get(sr_id)
                        captured_at = snapshot.captured_at or datetime.now(timezone.utc).replace(tzinfo=None)
                        # Use last_confirmed_at for freshness (fallback to captured_at for old data)
                        last_confirmed = snapshot.last_confirmed_at or captured_at
                        cached = snapshot_to_cached_from_models(
                            snapshot_id=snapshot.id,
                            event_id=betpawa_event_id,
                            bookmaker_id=0,
                            captured_at=captured_at,
                            last_confirmed_at=last_confirmed,
                            markets=markets,
                        )
                        self._odds_cache.put_competitor_snapshot(
                            event_id=betpawa_event_id,
                            source=source_value,
                            snapshot=cached,
                            kickoff=kickoff,
                        )
                        cache_updated += 1
                    except Exception as e:
                        logger.debug(
                            "Cache update failed for competitor snapshot",
                            competitor_event_id=snapshot.competitor_event_id,
                            error=str(e),
                        )

                cache_update_ms = int((time.perf_counter() - cache_update_start) * 1000)
                logger.debug(
                    "Cache updated",
                    snapshots=cache_updated,
                    duration_ms=cache_update_ms,
                )

            # Store timing breakdown for progress events
            self._last_storage_timings = {
                "storage_lookups_ms": storage_lookups_ms,
                "storage_processing_ms": storage_processing_ms,
                "storage_flush_ms": storage_flush_ms,
                "storage_commit_ms": storage_commit_ms,
                "cache_update_ms": cache_update_ms,
            }

            logger.info(
                "sync_path.storage_timing",
                storage_lookups_ms=storage_lookups_ms,
                storage_processing_ms=storage_processing_ms,
                storage_flush_ms=storage_flush_ms,
                storage_commit_ms=storage_commit_ms,
                cache_update_ms=cache_update_ms,
                bp_snapshots=len(betpawa_snapshots),
                comp_snapshots=len(competitor_snapshots),
            )

        logger.info(
            "Batch storage complete",
            batch_id=batch["batch_id"],
            events_stored=events_stored,
            snapshots_created=snapshots_created,
            errors=errors,
        )

        return {
            "events_stored": events_stored,
            "snapshots_created": snapshots_created,
            "errors": errors,
        }

    async def _get_bookmaker_ids(self, db: AsyncSession) -> dict[str, int]:
        """Get or create bookmaker IDs for all platforms.

        Creates bookmakers on first run if they don't exist (like v1.6 did).

        Args:
            db: AsyncSession for database operations.

        Returns:
            Dict mapping platform slug to bookmaker ID.
        """
        # Platform configuration for auto-creation
        platform_config = {
            "betpawa": {
                "name": "BetPawa",
                "base_url": "https://www.betpawa.ng",
            },
            "sportybet": {
                "name": "SportyBet",
                "base_url": "https://www.sportybet.com",
            },
            "bet9ja": {
                "name": "Bet9ja",
                "base_url": "https://sports.bet9ja.com",
            },
        }

        result = await db.execute(select(Bookmaker))
        bookmakers = result.scalars().all()
        bookmaker_map = {b.slug: b.id for b in bookmakers}

        # Create missing bookmakers (first run scenario)
        for slug, config in platform_config.items():
            if slug not in bookmaker_map:
                logger.info(
                    "Creating missing bookmaker",
                    slug=slug,
                    name=config["name"],
                )
                bookmaker = Bookmaker(
                    name=config["name"],
                    slug=slug,
                    base_url=config["base_url"],
                )
                db.add(bookmaker)
                await db.flush()  # Get ID without committing
                bookmaker_map[slug] = bookmaker.id

        return bookmaker_map

    async def _get_event_ids_by_sr_ids(
        self,
        db: AsyncSession,
        sr_ids: list[str],
    ) -> dict[str, int]:
        """Get Event IDs by SportRadar IDs.

        Args:
            db: AsyncSession for database operations.
            sr_ids: List of SportRadar IDs to look up.

        Returns:
            Dict mapping SR ID to Event ID.
        """
        if not sr_ids:
            return {}

        result = await db.execute(
            select(Event.id, Event.sportradar_id).where(
                Event.sportradar_id.in_(sr_ids)
            )
        )
        return {row.sportradar_id: row.id for row in result.all()}

    async def _get_competitor_event_ids_by_sr_ids(
        self,
        db: AsyncSession,
        sr_ids: list[str],
    ) -> dict[tuple[str, str], int]:
        """Get CompetitorEvent IDs by SportRadar IDs.

        Args:
            db: AsyncSession for database operations.
            sr_ids: List of SportRadar IDs to look up.

        Returns:
            Dict mapping (SR ID, source) to CompetitorEvent ID.
        """
        if not sr_ids:
            return {}

        result = await db.execute(
            select(CompetitorEvent.id, CompetitorEvent.sportradar_id, CompetitorEvent.source).where(
                CompetitorEvent.sportradar_id.in_(sr_ids)
            )
        )
        return {(row.sportradar_id, row.source): row.id for row in result.all()}

    async def _get_or_create_fallback_sport(self, db: AsyncSession) -> int:
        """Get or create Football sport for fallback tournament.

        Returns:
            Sport ID for Football.
        """
        result = await db.execute(
            select(Sport.id).where(Sport.slug == "football")
        )
        row = result.first()
        if row:
            return row[0]

        # Create Football sport
        sport = Sport(name="Football", slug="football")
        db.add(sport)
        await db.flush()
        return sport.id

    async def _get_or_create_fallback_tournament(
        self,
        db: AsyncSession,
        sport_id: int,
    ) -> int:
        """Get or create fallback tournament for BetPawa events discovered via scraping.

        Args:
            db: AsyncSession for database operations.
            sport_id: Sport ID for Football.

        Returns:
            Tournament ID for the fallback tournament.
        """
        fallback_name = "Discovered Events"
        result = await db.execute(
            select(Tournament.id).where(
                Tournament.name == fallback_name,
                Tournament.sport_id == sport_id,
            )
        )
        row = result.first()
        if row:
            return row[0]

        # Create fallback tournament
        tournament = Tournament(
            name=fallback_name,
            sport_id=sport_id,
            country=None,
            sportradar_id=None,
        )
        db.add(tournament)
        await db.flush()
        return tournament.id

    async def _get_or_create_fallback_competitor_tournament(
        self,
        db: AsyncSession,
        source: CompetitorSource,
        sport_id: int,
    ) -> int:
        """Get or create fallback competitor tournament for events discovered via scraping.

        Args:
            db: AsyncSession for database operations.
            source: Platform source (SPORTYBET or BET9JA).
            sport_id: Sport ID for Football.

        Returns:
            CompetitorTournament ID for the fallback tournament.
        """
        fallback_name = "Discovered Events"
        fallback_external_id = f"discovered-{source.value}"

        result = await db.execute(
            select(CompetitorTournament.id).where(
                CompetitorTournament.source == source.value,
                CompetitorTournament.external_id == fallback_external_id,
            )
        )
        row = result.first()
        if row:
            return row[0]

        # Create fallback competitor tournament
        tournament = CompetitorTournament(
            source=source.value,
            sport_id=sport_id,
            name=fallback_name,
            external_id=fallback_external_id,
            sportradar_id=None,
        )
        db.add(tournament)
        await db.flush()
        return tournament.id

    async def _get_or_create_competitor_tournament_from_raw(
        self,
        db: AsyncSession,
        source: CompetitorSource,
        raw_data: dict,
        sport_id: int,
    ) -> int:
        """Get or create CompetitorTournament from raw API response.

        Extracts tournament name and country from competitor raw response
        to create proper tournament records with country_raw populated.

        Args:
            db: AsyncSession for database operations.
            source: Platform source (SPORTYBET or BET9JA).
            raw_data: Raw API response from the competitor platform.
            sport_id: Sport ID for Football.

        Returns:
            CompetitorTournament ID.
        """
        if source == CompetitorSource.SPORTYBET:
            # SportyBet tournament/country is nested in sport.category structure
            # Structure: sport.category.name = country, sport.category.tournament.name = tournament
            sport_data = raw_data.get("sport", {})
            category_data = sport_data.get("category", {})
            tournament_data = category_data.get("tournament", {})

            tournament_name = tournament_data.get("name", "Unknown")
            country_raw = category_data.get("name")  # Country/region
            external_id = tournament_data.get("id", "")  # SportRadar tournament ID
        else:  # BET9JA
            # Bet9ja has GN (group name) and SG (sport group / country)
            tournament_name = raw_data.get("GN", "Unknown")
            country_raw = raw_data.get("SG")  # Sport group (country) - NOT "SGN"
            external_id = str(raw_data.get("GID", ""))  # Group ID

        if not external_id:
            # Generate fallback external_id
            external_id = f"discovered-{source.value}-{hash(tournament_name) % 10000}"

        # Try to find existing tournament by source and external_id
        result = await db.execute(
            select(CompetitorTournament.id).where(
                CompetitorTournament.source == source.value,
                CompetitorTournament.external_id == external_id,
            )
        )
        row = result.first()
        if row:
            return row[0]

        # Create new tournament with country
        tournament = CompetitorTournament(
            source=source.value,
            sport_id=sport_id,
            name=tournament_name,
            external_id=external_id,
            country_raw=country_raw,
            sportradar_id=None,
        )
        db.add(tournament)
        await db.flush()

        logger.debug(
            "Created competitor tournament from raw data",
            source=source.value,
            name=tournament_name,
            country_raw=country_raw,
            tournament_id=tournament.id,
        )

        return tournament.id

    async def _get_or_create_tournament_from_betpawa_raw(
        self,
        db: AsyncSession,
        raw_data: dict,
        sport_id: int,
    ) -> int:
        """Get or create Tournament from BetPawa event raw response.

        Parses competition and region info from raw_data to find/create a proper tournament.

        Args:
            db: AsyncSession for database operations.
            raw_data: Raw BetPawa event response containing competition/region.
            sport_id: Sport ID for Football.

        Returns:
            Tournament ID.
        """
        # Parse competition and region from raw_data
        competition = raw_data.get("competition", {})
        region = raw_data.get("region", {})

        comp_name = competition.get("name", "Unknown")
        comp_id = competition.get("id")
        region_name = region.get("name")

        # Try to find existing tournament by name
        result = await db.execute(
            select(Tournament.id).where(
                Tournament.name == comp_name,
                Tournament.sport_id == sport_id,
            )
        )
        row = result.first()
        if row:
            return row[0]

        # Create new tournament
        tournament = Tournament(
            name=comp_name,
            sport_id=sport_id,
            country=region_name,  # Use region name as country
            sportradar_id=None,  # BetPawa doesn't provide SR ID for tournaments in event data
        )
        db.add(tournament)
        await db.flush()

        logger.debug(
            "Created tournament from BetPawa raw data",
            name=comp_name,
            country=region_name,
            tournament_id=tournament.id,
        )

        return tournament.id

    async def _create_event_from_betpawa_raw(
        self,
        db: AsyncSession,
        sr_id: str,
        raw_data: dict,
        tournament_id: int,
        bookmaker_id: int,
        platform_id: str,
    ) -> int:
        """Create Event record from BetPawa raw API response.

        Args:
            db: AsyncSession for database operations.
            sr_id: SportRadar ID.
            raw_data: Raw BetPawa event response.
            tournament_id: FK to tournaments table.
            bookmaker_id: FK to bookmakers table.
            platform_id: BetPawa event ID.

        Returns:
            Event ID.
        """
        # Parse participants (teams) - position 1 = home, position 2 = away
        participants = raw_data.get("participants", [])
        home_team = "Unknown"
        away_team = "Unknown"

        for p in participants:
            if p.get("position") == 1:
                home_team = p.get("name", "Unknown")
            elif p.get("position") == 2:
                away_team = p.get("name", "Unknown")

        # Parse kickoff
        start_time = raw_data.get("startTime", "")
        try:
            kickoff = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            kickoff = kickoff.replace(tzinfo=None)  # Store as naive UTC
        except (ValueError, TypeError):
            kickoff = datetime.utcnow()

        # Create event
        name = raw_data.get("name", f"{home_team} - {away_team}")
        event = Event(
            sportradar_id=sr_id,
            tournament_id=tournament_id,
            name=name,
            home_team=home_team,
            away_team=away_team,
            kickoff=kickoff,
        )
        db.add(event)
        await db.flush()

        # Create event-bookmaker link
        event_bookmaker = EventBookmaker(
            event_id=event.id,
            bookmaker_id=bookmaker_id,
            external_event_id=platform_id,
        )
        db.add(event_bookmaker)
        await db.flush()

        logger.debug(
            "Created BetPawa event from raw data",
            sr_id=sr_id,
            event_id=event.id,
            name=name,
        )

        return event.id

    async def _create_competitor_event_from_raw(
        self,
        db: AsyncSession,
        sr_id: str,
        source: CompetitorSource,
        raw_data: dict,
        tournament_id: int,
        platform_id: str,
    ) -> int:
        """Create CompetitorEvent record from raw API response.

        Args:
            db: AsyncSession for database operations.
            sr_id: SportRadar ID.
            source: Platform source (SPORTYBET or BET9JA).
            raw_data: Raw API response.
            tournament_id: FK to competitor_tournaments table.
            platform_id: Platform-specific event ID.

        Returns:
            CompetitorEvent ID.
        """
        if source == CompetitorSource.SPORTYBET:
            # SportyBet format
            home_team = raw_data.get("homeTeamName", "Unknown")
            away_team = raw_data.get("awayTeamName", "Unknown")
            estimate_start = raw_data.get("estimateStartTime")
            try:
                kickoff = datetime.fromtimestamp(estimate_start / 1000, tz=timezone.utc)
                kickoff = kickoff.replace(tzinfo=None)
            except (ValueError, TypeError):
                kickoff = datetime.utcnow()
        else:
            # Bet9ja format - parse DS field "Home Team - Away Team"
            ds_field = raw_data.get("DS", "Unknown - Unknown")
            parts = ds_field.split(" - ", 1)
            home_team = parts[0].strip() if parts else "Unknown"
            away_team = parts[1].strip() if len(parts) > 1 else "Unknown"

            start_date_str = raw_data.get("STARTDATE", "")
            try:
                kickoff = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                kickoff = datetime.utcnow()

        name = f"{home_team} - {away_team}"

        # Look up BetPawa event by sportradar_id for cross-platform linking
        # (matches pattern from competitor_events.py:119)
        bp_event_result = await db.execute(
            select(Event.id).where(Event.sportradar_id == sr_id)
        )
        betpawa_event_id = bp_event_result.scalar_one_or_none()

        event = CompetitorEvent(
            source=source.value,
            tournament_id=tournament_id,
            sportradar_id=sr_id,
            external_id=platform_id,
            name=name,
            home_team=home_team,
            away_team=away_team,
            kickoff=kickoff,
            betpawa_event_id=betpawa_event_id,
        )
        db.add(event)
        await db.flush()

        logger.debug(
            "Created competitor event from raw data",
            sr_id=sr_id,
            source=source.value,
            event_id=event.id,
            name=name,
        )

        return event.id

    async def _ensure_event_bookmaker(
        self,
        db: AsyncSession,
        event_id: int,
        bookmaker_id: int,
        external_event_id: str,
    ) -> None:
        """Ensure EventBookmaker record exists for a platform.

        Creates the link between a BetPawa Event and another bookmaker if it doesn't exist.
        This enables the min_bookmakers filter to work for cross-platform events.

        Args:
            db: AsyncSession for database operations.
            event_id: FK to events table.
            bookmaker_id: FK to bookmakers table.
            external_event_id: Platform-specific event ID.
        """
        # Check if EventBookmaker already exists
        result = await db.execute(
            select(EventBookmaker.id).where(
                EventBookmaker.event_id == event_id,
                EventBookmaker.bookmaker_id == bookmaker_id,
            )
        )
        if result.first() is not None:
            return  # Already exists

        # Create new EventBookmaker
        link = EventBookmaker(
            event_id=event_id,
            bookmaker_id=bookmaker_id,
            external_event_id=external_event_id,
        )
        db.add(link)
        await db.flush()

        logger.debug(
            "Created EventBookmaker link",
            event_id=event_id,
            bookmaker_id=bookmaker_id,
            external_event_id=external_event_id,
        )

    def _parse_betpawa_markets(self, raw_data: dict) -> list[MarketOdds]:
        """Parse BetPawa raw response into MarketOdds records.

        BetPawa markets ARE the canonical format - no mapping needed.
        Direct extraction from the markets array.

        Args:
            raw_data: Raw API response from BetPawa (full event data).

        Returns:
            List of MarketOdds objects (snapshot_id will be set later).
        """
        market_odds_list: list[MarketOdds] = []
        markets = raw_data.get("markets", [])

        for market_data in markets:
            market_type = market_data.get("marketType", {})
            market_id = market_type.get("id")

            if not market_id:
                continue

            # Extract market_groups from tabs array
            # Tabs are like ["all", "popular"], ["all", "popular", "goals"], etc.
            # Store all non-"all" tabs so markets appear in multiple category tabs
            tabs = market_type.get("tabs", [])
            market_groups = [t for t in tabs if t != "all"]
            if not market_groups:
                market_groups = ["other"]

            for row in market_data.get("row", []):
                prices = row.get("prices", [])
                line = row.get("formattedHandicap")

                # Parse line to float if present
                line_value = None
                if line:
                    try:
                        line_value = float(line)
                    except (ValueError, TypeError):
                        line_value = None

                if line_value is None and prices:
                    # Fall back to handicap from first price
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
                    market_groups=market_groups,
                )
                market_odds_list.append(market_odds)

        return market_odds_list

    def _parse_sportybet_markets(self, raw_data: dict) -> list[CompetitorMarketOdds]:
        """Parse SportyBet raw response into CompetitorMarketOdds records.

        Args:
            raw_data: Raw API response from SportyBet (event data).

        Returns:
            List of CompetitorMarketOdds objects (snapshot_id will be set later).
        """
        market_odds_list: list[CompetitorMarketOdds] = []
        markets = raw_data.get("markets", [])

        for market_data in markets:
            try:
                # Parse into Pydantic model
                sportybet_market = SportybetMarket.model_validate(market_data)

                # Map to Betpawa format
                mapped = map_sportybet_to_betpawa(sportybet_market)

                # Convert MappedMarket to CompetitorMarketOdds
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
                    line=mapped.line if mapped.line is not None else (mapped.handicap.home if mapped.handicap else None),
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
                logger.debug("Error parsing SportyBet market", error=str(e))

        return market_odds_list

    def _parse_bet9ja_markets(self, raw_data: dict) -> list[CompetitorMarketOdds]:
        """Parse Bet9ja raw response into CompetitorMarketOdds records.

        Args:
            raw_data: Raw API response from Bet9ja (event data).

        Returns:
            List of CompetitorMarketOdds objects (snapshot_id will be set later).
        """
        market_odds_list: list[CompetitorMarketOdds] = []

        # Bet9ja odds are nested inside the "O" object
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

                market_odds = CompetitorMarketOdds(
                    betpawa_market_id=mapped.betpawa_market_id,
                    betpawa_market_name=mapped.betpawa_market_name,
                    line=mapped.line if mapped.line is not None else (mapped.handicap.home if mapped.handicap else None),
                    handicap_type=mapped.handicap.type if mapped.handicap else None,
                    handicap_home=mapped.handicap.home if mapped.handicap else None,
                    handicap_away=mapped.handicap.away if mapped.handicap else None,
                    outcomes=outcomes,
                )
                market_odds_list.append(market_odds)

        except Exception as e:
            logger.warning("Error parsing Bet9ja markets", error=str(e))

        return market_odds_list

    # =========================================================================
    # FULL CYCLE: Complete scrape orchestration
    # =========================================================================

    async def run_full_cycle(
        self,
        db: AsyncSession,
        scrape_run_id: int,
    ) -> AsyncGenerator[dict, None]:
        """Run a complete scrape cycle: discovery -> queue -> scrape -> store.

        This method orchestrates the full event-centric scraping pipeline:
        1. Discovery: Parallel discovery from all platforms
        2. Build queue: Priority queue based on kickoff + coverage
        3. Process batches: Scrape all platforms per event, store results
        4. Cleanup: Clear coordinator state for next cycle

        Yields SSE-compatible progress events at each stage.

        Args:
            db: AsyncSession for database operations.
            scrape_run_id: FK to scrape_runs.id for tracking.

        Yields:
            Progress dicts with event_type and relevant data for SSE streaming.
        """
        # Phase 1: Cycle start
        yield {
            "event_type": "CYCLE_START",
            "scrape_run_id": scrape_run_id,
        }

        # Phase 2: Discovery
        await self.discover_events()

        discovery_counts = {
            platform: sum(
                1 for e in self._event_map.values()
                if platform in e.platforms
            )
            for platform in ["betpawa", "sportybet", "bet9ja"]
        }

        yield {
            "event_type": "DISCOVERY_COMPLETE",
            "discovery_counts": discovery_counts,
            "total_events": len(self._event_map),
            **self._last_discovery_timings,
        }

        # Phase 3: Build queue
        self.build_priority_queue()
        batch_count = (len(self._priority_queue) + self._batch_size - 1) // self._batch_size

        yield {
            "event_type": "QUEUE_BUILT",
            "total_events": len(self._event_map),
            "batch_count": batch_count,
            "batch_size": self._batch_size,
            "queue_stats": self.get_queue_stats(),
        }

        # Phase 4: Process batches
        batch_index = 0
        events_scraped = 0
        events_failed = 0
        total_snapshots = 0
        total_start = time.perf_counter()

        while batch := self.get_next_batch():
            batch_start = time.perf_counter()

            yield {
                "event_type": "BATCH_START",
                "batch_id": batch["batch_id"],
                "batch_index": batch_index,
                "batch_count": batch_count,
                "event_count": len(batch["events"]),
            }

            # Scrape batch concurrently and yield per-event progress
            progress_events = await self.scrape_batch(batch)
            for progress in progress_events:
                yield progress

            batch_scrape_ms = int((time.perf_counter() - batch_start) * 1000)

            # Store results
            store_start = time.perf_counter()
            store_result = await self.store_batch_results(db, batch, scrape_run_id)
            store_ms = int((time.perf_counter() - store_start) * 1000)

            # Count successes and failures
            batch_success = sum(
                1 for e in batch["events"]
                if e.status == ScrapeStatus.COMPLETED
            )
            batch_failed = len(batch["events"]) - batch_success

            yield {
                "event_type": "BATCH_COMPLETE",
                "batch_id": batch["batch_id"],
                "batch_index": batch_index,
                "events_stored": store_result["events_stored"],
                "snapshots_created": store_result["snapshots_created"],
                "errors": store_result["errors"],
                "batch_scrape_ms": batch_scrape_ms,
                "batch_store_ms": store_ms,
                **self._last_storage_timings,
            }

            batch_index += 1
            events_scraped += batch_success
            events_failed += batch_failed
            total_snapshots += store_result["snapshots_created"]

        # Phase 5: Cycle complete
        total_ms = int((time.perf_counter() - total_start) * 1000)

        yield {
            "event_type": "CYCLE_COMPLETE",
            "scrape_run_id": scrape_run_id,
            "total_events": len(self._event_map),
            "events_scraped": events_scraped,
            "events_failed": events_failed,
            "total_snapshots": total_snapshots,
            "batch_count": batch_index,
            "total_timing_ms": total_ms,
        }

        # Clear for next cycle
        self.clear()
