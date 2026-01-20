"""Scraping orchestrator for concurrent platform execution."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.schemas import Platform, PlatformResult, ScrapeResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


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
                platform, sport_id, competition_id, include_data, timeout
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

        # Commit any logged errors
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
    ) -> tuple[list[dict], int]:
        """Scrape a single platform with timeout.

        Args:
            platform: Platform to scrape.
            sport_id: Filter to specific sport (e.g., "2" for football).
            competition_id: Filter to specific competition.
            include_data: Whether to return event data.
            timeout: Timeout in seconds.

        Returns:
            Tuple of (events list, duration in ms).

        Raises:
            asyncio.TimeoutError: If operation exceeds timeout.
            Exception: Any error from the underlying client.
        """
        start_time = time.perf_counter()

        async def _do_scrape() -> list[dict]:
            client = self._clients[platform]

            # For now, check health as a simple scrape operation
            # Full implementation will fetch actual events using filters
            # Filters (sport_id, competition_id) are accepted but not yet
            # fully implemented for event fetching
            if platform == Platform.BETPAWA:
                # BetPawa has fetch_categories - use that for discovery
                await client.fetch_categories()
                # Return empty list for now - actual event fetching will be enhanced
                return []
            elif platform == Platform.SPORTYBET:
                # SportyBet requires specific event IDs
                # Return empty list for now
                return []
            elif platform == Platform.BET9JA:
                # Bet9ja has fetch_sports for discovery
                await client.fetch_sports()
                return []
            else:
                return []

        # Apply timeout
        events = await asyncio.wait_for(_do_scrape(), timeout=timeout)

        end_time = time.perf_counter()
        duration_ms = int((end_time - start_time) * 1000)

        return events, duration_ms

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
