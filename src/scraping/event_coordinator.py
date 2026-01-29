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
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog

from src.scraping.schemas.coordinator import EventTarget, ScrapeBatch, ScrapeStatus

if TYPE_CHECKING:
    from src.scraping.clients.bet9ja import Bet9jaClient
    from src.scraping.clients.betpawa import BetPawaClient
    from src.scraping.clients.sportybet import SportyBetClient

logger = structlog.get_logger(__name__)


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

                if sr_id in self._event_map:
                    # Event already discovered from another platform - add this platform
                    self._event_map[sr_id].platforms.add(platform)
                else:
                    # New event - create EventTarget
                    self._event_map[sr_id] = EventTarget(
                        sr_id=sr_id,
                        kickoff=kickoff,
                        platforms={platform},
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
        """Parse a BetPawa event and extract SR ID.

        Args:
            event_data: Raw event data from BetPawa API.
            now: Current UTC time for filtering started events.

        Returns:
            Dict with {sr_id, kickoff} or None if not parseable/started.
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

        return {"sr_id": sr_id, "kickoff": kickoff}

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
        """Parse a SportyBet event and extract SR ID.

        Args:
            event_data: Raw event data from SportyBet API.
            now: Current UTC time for filtering started events.

        Returns:
            Dict with {sr_id, kickoff} or None if not parseable/started.
        """
        # Extract SR ID from eventId (format: "sr:match:12345678")
        event_id = event_data.get("eventId", "")
        if not event_id.startswith("sr:match:"):
            return None

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

        return {"sr_id": sr_id, "kickoff": kickoff}

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
        """Parse a Bet9ja event and extract SR ID.

        Args:
            event_data: Raw event data from Bet9ja API.
            now: Current UTC time for filtering started events.

        Returns:
            Dict with {sr_id, kickoff} or None if not parseable/started.
        """
        # Extract SR ID from EXTID field
        sr_id = event_data.get("EXTID")
        if not sr_id:
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

        return {"sr_id": sr_id, "kickoff": kickoff}

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
