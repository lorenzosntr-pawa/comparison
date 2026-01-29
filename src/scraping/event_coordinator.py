"""Event-centric scraping coordinator.

This module implements the EventCoordinator class which:
1. Discovers events from all platforms in parallel
2. Builds a unified priority queue based on kickoff urgency and coverage
3. Provides batched event access for parallel scraping (Phase 38)

The coordinator is the orchestration layer for the new event-centric architecture
that replaces the sequential platform-by-platform scraping approach.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.bookmaker import Bookmaker
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
    CompetitorSource,
)
from src.db.models.event import Event
from src.db.models.event_scrape_status import EventScrapeStatus
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.market_mapping.mappers.bet9ja import map_bet9ja_odds_to_betpawa
from src.market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from src.market_mapping.types.errors import MappingError
from src.market_mapping.types.sportybet import SportybetMarket
from src.scraping.schemas.coordinator import EventTarget, ScrapeBatch, ScrapeStatus

if TYPE_CHECKING:
    from src.scraping.clients.bet9ja import Bet9jaClient
    from src.scraping.clients.betpawa import BetPawaClient
    from src.scraping.clients.sportybet import SportyBetClient

logger = structlog.get_logger(__name__)

# Platform concurrency limits (from Phase 36 rate limit investigation)
PLATFORM_SEMAPHORES = {
    "betpawa": 50,
    "sportybet": 50,
    "bet9ja": 15,
}
BET9JA_DELAY_MS = 25  # 25ms delay after each Bet9ja request


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
        batch_size: int = 50,
    ) -> None:
        """Initialize the EventCoordinator.

        Args:
            betpawa_client: BetPawa API client.
            sportybet_client: SportyBet API client.
            bet9ja_client: Bet9ja API client.
            batch_size: Number of events per batch (default 50).
        """
        self._clients: dict[str, BetPawaClient | SportyBetClient | Bet9jaClient] = {
            "betpawa": betpawa_client,
            "sportybet": sportybet_client,
            "bet9ja": bet9ja_client,
        }
        self._batch_size = batch_size
        self._event_map: dict[str, EventTarget] = {}
        self._priority_queue: list[EventTarget] = []

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

        # Run discovery in parallel
        results = await asyncio.gather(
            self._discover_betpawa(),
            self._discover_sportybet(),
            self._discover_bet9ja(),
            return_exceptions=True,
        )

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

        logger.info(
            "Event discovery complete",
            betpawa=discovery_counts.get("betpawa", 0),
            sportybet=discovery_counts.get("sportybet", 0),
            bet9ja=discovery_counts.get("bet9ja", 0),
            merged=len(self._event_map),
        )

        return self._event_map

    async def _discover_betpawa(self) -> list[dict]:
        """Discover events from BetPawa.

        Fetches all football competitions, then fetches events from each.
        Extracts SR IDs from the SPORTRADAR widget in each event.

        Returns:
            List of dicts with {sr_id, kickoff} for each upcoming event.
        """
        logger.debug("Discovering BetPawa events")
        events: list[dict] = []
        now = datetime.now(timezone.utc)

        try:
            client = self._clients["betpawa"]
            # Fetch competition list
            categories_data = await client.fetch_categories()

            # Extract competition IDs from the nested structure
            competition_ids: list[str] = []
            regions = categories_data.get("regions", [])
            for region in regions:
                competitions = region.get("competitions", [])
                for comp in competitions:
                    comp_id = str(comp.get("id", ""))
                    if comp_id:
                        competition_ids.append(comp_id)

            logger.debug(
                "Found BetPawa competitions",
                count=len(competition_ids),
            )

            # Fetch events from each competition with semaphore
            semaphore = asyncio.Semaphore(5)

            async def fetch_comp_events(comp_id: str) -> list[dict]:
                async with semaphore:
                    try:
                        data = await client.fetch_events(comp_id)
                        # Parse events from response
                        comp_events: list[dict] = []
                        event_lists = data.get("eventLists", [])
                        for event_list in event_lists:
                            for event_data in event_list.get("events", []):
                                parsed = self._parse_betpawa_event(event_data, now)
                                if parsed:
                                    comp_events.append(parsed)
                        return comp_events
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

            logger.debug("Discovered BetPawa events", count=len(events))

        except Exception as e:
            logger.error("BetPawa discovery failed", error=str(e))
            return []

        return events

    def _parse_betpawa_event(
        self,
        event_data: dict,
        now: datetime,
    ) -> dict | None:
        """Parse a BetPawa event and extract SR ID and platform ID.

        Args:
            event_data: Raw event data from BetPawa API.
            now: Current UTC time for filtering started events.

        Returns:
            Dict with {sr_id, kickoff, platform_id} or None if not parseable/started.
        """
        # Extract SR ID from widgets array
        widgets = event_data.get("widgets", [])
        sr_id = None
        for widget in widgets:
            if widget.get("type") == "SPORTRADAR":
                # Widget data format: {"matchId": "12345678", ...}
                widget_data = widget.get("data", {})
                sr_id = str(widget_data.get("matchId", ""))
                break

        if not sr_id:
            return None

        # Extract BetPawa platform-specific event ID
        platform_id = str(event_data.get("id", ""))
        if not platform_id:
            return None

        # Parse kickoff time
        start_time_str = event_data.get("startTime")
        if not start_time_str:
            return None

        try:
            # BetPawa format: "2026-01-30T15:00:00Z"
            kickoff = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

        # Filter out started events
        if kickoff <= now:
            return None

        return {"sr_id": sr_id, "kickoff": kickoff, "platform_id": platform_id}

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

        async def scrape_platform(platform: str) -> tuple[str, dict | None, str | None]:
            """Scrape a single platform for this event."""
            # Check if we have the platform ID
            platform_id = event.platform_ids.get(platform)
            if not platform_id:
                return (platform, None, "No platform ID available")

            try:
                async with semaphores[platform]:
                    client = self._clients[platform]
                    result = await client.fetch_event(platform_id)

                    # Add delay for Bet9ja to avoid rate limiting
                    if platform == "bet9ja":
                        await asyncio.sleep(BET9JA_DELAY_MS / 1000)

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
        }

    async def scrape_batch(
        self,
        batch: ScrapeBatch,
    ) -> AsyncGenerator[dict, None]:
        """Scrape all events in batch, yielding progress for each.

        Processes events sequentially in priority order. For each event,
        scrapes all platforms in parallel, updates event status and results,
        and yields progress events for SSE streaming.

        Args:
            batch: ScrapeBatch containing events to scrape.

        Yields:
            Progress dicts with event_type, sr_id, and platform results.
        """
        # Create semaphores for all platforms (reuse across batch)
        semaphores = {
            platform: asyncio.Semaphore(limit)
            for platform, limit in PLATFORM_SEMAPHORES.items()
        }

        logger.debug(
            "Starting batch scrape",
            batch_id=batch["batch_id"],
            event_count=len(batch["events"]),
        )

        for event in batch["events"]:
            # Mark event as in progress
            event.status = ScrapeStatus.IN_PROGRESS

            # Yield "scraping started" progress event
            yield {
                "event_type": "EVENT_SCRAPING",
                "sr_id": event.sr_id,
                "platforms_pending": list(event.platforms),
            }

            # Scrape all platforms in parallel
            result = await self._scrape_event_all_platforms(event, semaphores)

            # Update event with results
            event.results = result["data"]
            event.errors = result["errors"]

            # Determine final status
            if result["errors"]:
                # Some platforms failed
                if result["data"]:
                    # Partial success - at least some data
                    event.status = ScrapeStatus.COMPLETED
                else:
                    # Complete failure - no data at all
                    event.status = ScrapeStatus.FAILED
            else:
                # All platforms succeeded
                event.status = ScrapeStatus.COMPLETED

            # Yield "scraping complete" progress event
            yield {
                "event_type": "EVENT_SCRAPED",
                "sr_id": event.sr_id,
                "platforms_scraped": list(result["data"].keys()),
                "platforms_failed": list(result["errors"].keys()),
                "timing_ms": result["timing_ms"],
            }

        logger.debug(
            "Batch scrape complete",
            batch_id=batch["batch_id"],
        )

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

        # Pre-fetch bookmaker IDs
        bookmaker_ids = await self._get_bookmaker_ids(db)

        # Pre-fetch event mappings (SR ID -> DB event ID)
        sr_ids = [event.sr_id for event in batch["events"]]
        event_id_map = await self._get_event_ids_by_sr_ids(db, sr_ids)

        # Pre-fetch competitor event mappings (SR ID -> CompetitorEvent ID by source)
        competitor_event_map = await self._get_competitor_event_ids_by_sr_ids(db, sr_ids)

        # Collect all records for bulk operations
        status_records: list[EventScrapeStatus] = []
        betpawa_snapshots: list[tuple[OddsSnapshot, list[MarketOdds]]] = []
        competitor_snapshots: list[tuple[CompetitorOddsSnapshot, list[CompetitorMarketOdds]]] = []

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
                        event_id = event_id_map.get(event.sr_id)
                        if event_id is None:
                            logger.debug(
                                "No DB event for BetPawa result",
                                sr_id=event.sr_id,
                            )
                            continue

                        bookmaker_id = bookmaker_ids.get("betpawa")
                        if bookmaker_id is None:
                            continue

                        # Create snapshot
                        snapshot = OddsSnapshot(
                            event_id=event_id,
                            bookmaker_id=bookmaker_id,
                            scrape_run_id=scrape_run_id,
                            raw_response=raw_data,
                        )

                        # Parse markets
                        markets = self._parse_betpawa_markets(raw_data)
                        betpawa_snapshots.append((snapshot, markets))
                        snapshots_created += 1

                    else:
                        # SportyBet/Bet9ja -> CompetitorOddsSnapshot + CompetitorMarketOdds
                        source = CompetitorSource.SPORTYBET if platform == "sportybet" else CompetitorSource.BET9JA
                        competitor_event_id = competitor_event_map.get((event.sr_id, source.value))

                        if competitor_event_id is None:
                            logger.debug(
                                "No competitor event for result",
                                sr_id=event.sr_id,
                                platform=platform,
                            )
                            continue

                        # Create competitor snapshot
                        snapshot = CompetitorOddsSnapshot(
                            competitor_event_id=competitor_event_id,
                            scrape_run_id=scrape_run_id,
                            raw_response=raw_data,
                        )

                        # Parse markets based on platform
                        if platform == "sportybet":
                            markets = self._parse_sportybet_markets(raw_data)
                        else:  # bet9ja
                            markets = self._parse_bet9ja_markets(raw_data)

                        competitor_snapshots.append((snapshot, markets))
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

        # Bulk insert all records (sequential for session safety)
        # Insert EventScrapeStatus records
        for status_record in status_records:
            db.add(status_record)

        # Insert BetPawa snapshots and markets
        for snapshot, markets in betpawa_snapshots:
            db.add(snapshot)
            await db.flush()  # Get snapshot ID
            for market in markets:
                market.snapshot_id = snapshot.id
                db.add(market)

        # Insert competitor snapshots and markets
        for snapshot, markets in competitor_snapshots:
            db.add(snapshot)
            await db.flush()  # Get snapshot ID
            for market in markets:
                market.snapshot_id = snapshot.id
                db.add(market)

        # Commit all changes
        await db.commit()

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
        """Get bookmaker IDs for all platforms.

        Args:
            db: AsyncSession for database operations.

        Returns:
            Dict mapping platform slug to bookmaker ID.
        """
        result = await db.execute(select(Bookmaker))
        bookmakers = result.scalars().all()
        return {b.slug: b.id for b in bookmakers}

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
                    line=mapped.line,
                    handicap_type=mapped.handicap.type if mapped.handicap else None,
                    handicap_home=mapped.handicap.home if mapped.handicap else None,
                    handicap_away=mapped.handicap.away if mapped.handicap else None,
                    outcomes=outcomes,
                )
                market_odds_list.append(market_odds)

        except Exception as e:
            logger.warning("Error parsing Bet9ja markets", error=str(e))

        return market_odds_list
