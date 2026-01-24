"""Scraping orchestrator for concurrent platform execution."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import structlog
import structlog.contextvars
from sqlalchemy import select, update

from src.db.models.bookmaker import Bookmaker
from src.db.models.event import Event
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.db.models.scrape import ScrapePhaseLog, ScrapeRun
from src.market_mapping.mappers.bet9ja import map_bet9ja_odds_to_betpawa
from src.market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from src.market_mapping.types.errors import MappingError
from src.market_mapping.types.sportybet import SportybetMarket
from src.matching.service import EventMatchingService
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.exceptions import InvalidEventIdError
from src.scraping.schemas import (
    Platform,
    PlatformResult,
    ScrapeErrorContext,
    ScrapePhase,
    ScrapeProgress,
    ScrapeResult,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.scraping.competitor_events import CompetitorEventScrapingService

logger = structlog.get_logger(__name__)


class ScrapingOrchestrator:
    """Orchestrates concurrent scraping across all platforms."""

    def __init__(
        self,
        sportybet_client: SportyBetClient,
        betpawa_client: BetPawaClient,
        bet9ja_client: Bet9jaClient,
        competitor_service: "CompetitorEventScrapingService | None" = None,
    ) -> None:
        """Initialize with client instances.

        Args:
            sportybet_client: Async SportyBet client.
            betpawa_client: Async BetPawa client.
            bet9ja_client: Async Bet9ja client.
            competitor_service: Optional CompetitorEventScrapingService for
                full-palimpsest competitor scraping. When provided, scrape_with_progress
                will use this service for SportyBet/Bet9ja instead of the old
                sportradar_id-filtered approach.
        """
        self._clients = {
            Platform.SPORTYBET: sportybet_client,
            Platform.BETPAWA: betpawa_client,
            Platform.BET9JA: bet9ja_client,
        }
        self._competitor_service = competitor_service

    async def _emit_phase(
        self,
        db: AsyncSession | None,
        scrape_run_id: int | None,
        platform: Platform | None,
        phase: ScrapePhase,
        message: str,
        events_count: int = 0,
        error: ScrapeErrorContext | None = None,
    ) -> ScrapeProgress:
        """Emit phase transition: update DB, log, return progress object."""
        # 1. Update ScrapeRun current state in DB
        if db and scrape_run_id:
            await db.execute(
                update(ScrapeRun)
                .where(ScrapeRun.id == scrape_run_id)
                .values(
                    current_phase=phase.value,
                    current_platform=platform.value if platform else None,
                )
            )
            # Don't commit - batch with other operations

        # 2. Log phase transition with structlog
        log = logger.bind(
            scrape_run_id=scrape_run_id,
            platform=platform.value if platform else None,
            phase=phase.value,
            events_count=events_count,
        )
        if error:
            log.error("phase_transition", error_type=error.error_type, error_message=error.error_message)
        else:
            log.info("phase_transition", message=message)

        # 3. Return progress object for SSE
        return ScrapeProgress(
            scrape_run_id=scrape_run_id,
            platform=platform,
            phase=phase,
            current=0,  # Will be set by caller
            total=0,    # Will be set by caller
            events_count=events_count,
            message=message,
            error=error,
        )

    async def _log_phase_history(
        self,
        db: AsyncSession,
        scrape_run_id: int,
        platform: Platform | None,
        phase: ScrapePhase,
        message: str,
        events_count: int = 0,
        error: ScrapeErrorContext | None = None,
    ) -> None:
        """Persist phase transition to history table."""
        phase_log = ScrapePhaseLog(
            scrape_run_id=scrape_run_id,
            platform=platform.value if platform else None,
            phase=phase.value,
            events_processed=events_count,
            message=message,
            error_details=error.model_dump() if error else None,
        )
        db.add(phase_log)
        # Don't commit - batch with other operations

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

    async def scrape_with_progress(
        self,
        platforms: list[Platform] | None = None,
        sport_id: str | None = None,
        competition_id: str | None = None,
        timeout: float = 30.0,
        scrape_run_id: int | None = None,
        db: AsyncSession | None = None,
    ) -> AsyncGenerator[ScrapeProgress, None]:
        """Scrape all platforms, yielding progress updates.

        Same as scrape_all() but yields ScrapeProgress updates before and after
        each platform scrape. Useful for SSE streaming to clients.

        When competitor_service is configured, uses full-palimpsest approach:
        - BetPawa scrapes to events table (unchanged)
        - Competitors scrape to competitor_events table (parallel, independent)

        When competitor_service is NOT configured (backwards compatibility):
        - Collects SportRadar IDs from BetPawa scrape
        - Passes IDs to SportyBet/Bet9ja for filtered matching

        Args:
            platforms: List of platforms to scrape (default: all).
            sport_id: Filter to specific sport (e.g., "2" for football).
            competition_id: Filter to specific competition.
            timeout: Per-platform timeout in seconds.
            scrape_run_id: Optional ScrapeRun ID for error logging.
            db: Optional database session for error logging.

        Yields:
            ScrapeProgress updates for each stage of scraping.
        """
        # Bind structlog context for this scrape run
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(scrape_run_id=scrape_run_id)

        # Determine if using new parallel competitor flow or legacy flow
        use_competitor_service = self._competitor_service is not None and db is not None

        if use_competitor_service:
            # NEW FLOW: BetPawa + parallel competitor scraping
            async for progress in self._scrape_with_competitor_service(
                sport_id, competition_id, timeout, scrape_run_id, db
            ):
                yield progress
        else:
            # LEGACY FLOW: Sequential with sportradar_id filtering
            async for progress in self._scrape_legacy_flow(
                platforms, sport_id, competition_id, timeout, scrape_run_id, db
            ):
                yield progress

    async def _scrape_with_competitor_service(
        self,
        sport_id: str | None,
        competition_id: str | None,
        timeout: float,
        scrape_run_id: int | None,
        db: AsyncSession,
    ) -> AsyncGenerator[ScrapeProgress, None]:
        """Scrape using new parallel competitor service flow.

        Flow:
        1. Scrape BetPawa (stores to events table)
        2. Scrape competitors in parallel using CompetitorEventScrapingService
           (stores to competitor_events table)

        Args:
            sport_id: Filter to specific sport.
            competition_id: Filter to specific competition.
            timeout: Per-platform timeout in seconds.
            scrape_run_id: Optional ScrapeRun ID.
            db: Database session.

        Yields:
            ScrapeProgress updates.
        """
        # 2 phases: BetPawa + Competitors
        total_phases = 2
        total_events = 0
        competitor_events = 0

        # Log and persist initializing phase
        logger.info("scrape_starting", mode="parallel_competitor", phases=total_phases)
        if scrape_run_id:
            await self._log_phase_history(
                db, scrape_run_id, None, ScrapePhase.INITIALIZING,
                f"Starting parallel scrape (BetPawa + Competitors)"
            )

        # Yield starting progress
        progress = await self._emit_phase(
            db, scrape_run_id, None, ScrapePhase.INITIALIZING,
            f"Starting parallel scrape (BetPawa + Competitors)"
        )
        progress.current = 0
        progress.total = total_phases
        yield progress

        # Phase 1: Scrape BetPawa
        betpawa_start_time = time.perf_counter()
        logger.info("platform_scrape_start", platform="betpawa", index=0)
        if scrape_run_id:
            await self._log_phase_history(
                db, scrape_run_id, Platform.BETPAWA, ScrapePhase.SCRAPING,
                "Scraping betpawa..."
            )

        progress = await self._emit_phase(
            db, scrape_run_id, Platform.BETPAWA, ScrapePhase.SCRAPING,
            "Scraping betpawa..."
        )
        progress.current = 0
        progress.total = total_phases
        yield progress

        try:
            events, duration_ms = await self._scrape_platform(
                Platform.BETPAWA, sport_id, competition_id, False, timeout, db
            )

            logger.info("platform_scrape_complete", platform="betpawa", events_count=len(events), duration_ms=duration_ms)

            # Store BetPawa events
            if events:
                if scrape_run_id:
                    await self._log_phase_history(
                        db, scrape_run_id, Platform.BETPAWA, ScrapePhase.STORING,
                        f"Storing {len(events)} betpawa events...",
                        events_count=len(events)
                    )

                progress = await self._emit_phase(
                    db, scrape_run_id, Platform.BETPAWA, ScrapePhase.STORING,
                    f"Storing {len(events)} betpawa events...",
                    events_count=len(events)
                )
                progress.current = 0
                progress.total = total_phases
                yield progress

                try:
                    await self._store_events(db, Platform.BETPAWA, events)
                except Exception as e:
                    logger.error("storage_failed", platform="betpawa", error=str(e), exc_info=True)
                    if scrape_run_id:
                        await db.rollback()
                        await self._log_error(db, scrape_run_id, Platform.BETPAWA, e)

            total_events += len(events)

            # Log BetPawa completion
            if scrape_run_id:
                await self._log_phase_history(
                    db, scrape_run_id, Platform.BETPAWA, ScrapePhase.COMPLETED,
                    f"Scraped {len(events)} events from betpawa ({duration_ms}ms)",
                    events_count=len(events)
                )

            progress = await self._emit_phase(
                db, scrape_run_id, Platform.BETPAWA, ScrapePhase.COMPLETED,
                f"Scraped {len(events)} events from betpawa ({duration_ms}ms)",
                events_count=len(events)
            )
            progress.current = 1
            progress.total = total_phases
            progress.duration_ms = duration_ms
            yield progress

        except Exception as e:
            error_ctx = self._create_error_context(e, Platform.BETPAWA, timeout)
            logger.error("platform_scrape_failed", platform="betpawa", error_type=error_ctx.error_type, error_message=error_ctx.error_message)

            if scrape_run_id:
                await db.rollback()
                await self._log_error(db, scrape_run_id, Platform.BETPAWA, e)
                await self._log_phase_history(
                    db, scrape_run_id, Platform.BETPAWA, ScrapePhase.FAILED,
                    f"Failed: {error_ctx.error_message}",
                    error=error_ctx
                )

            elapsed_ms = int((time.perf_counter() - betpawa_start_time) * 1000)
            progress = await self._emit_phase(
                db, scrape_run_id, Platform.BETPAWA, ScrapePhase.FAILED,
                f"Failed: {error_ctx.error_message}",
                error=error_ctx
            )
            progress.current = 1
            progress.total = total_phases
            progress.elapsed_ms = elapsed_ms
            yield progress

        # Phase 2: Scrape Competitors in parallel
        competitor_start_time = time.perf_counter()
        logger.info("competitor_scrape_start", mode="parallel")
        if scrape_run_id:
            await self._log_phase_history(
                db, scrape_run_id, None, ScrapePhase.SCRAPING,
                "Scraping competitors (SportyBet + Bet9ja)..."
            )

        progress = await self._emit_phase(
            db, scrape_run_id, None, ScrapePhase.SCRAPING,
            "Scraping competitors (SportyBet + Bet9ja)..."
        )
        progress.current = 1
        progress.total = total_phases
        yield progress

        try:
            # Run competitor scrapes sequentially to avoid session conflicts
            # (AsyncSession cannot be shared across concurrent tasks)
            assert self._competitor_service is not None

            sportybet_events = 0
            bet9ja_events = 0

            # SportyBet first
            try:
                sportybet_result = await self._competitor_service.scrape_sportybet_events(
                    db, scrape_run_id
                )
                if isinstance(sportybet_result, dict):
                    sportybet_events = sportybet_result.get("new", 0) + sportybet_result.get("updated", 0)
                    logger.info("sportybet_scrape_complete", **sportybet_result)
            except Exception as e:
                logger.error("sportybet_scrape_failed", error=str(e))

            # Then Bet9ja
            try:
                bet9ja_result = await self._competitor_service.scrape_bet9ja_events(
                    db, scrape_run_id
                )
                if isinstance(bet9ja_result, dict):
                    bet9ja_events = bet9ja_result.get("new", 0) + bet9ja_result.get("updated", 0)
                    logger.info("bet9ja_scrape_complete", **bet9ja_result)
            except Exception as e:
                logger.error("bet9ja_scrape_failed", error=str(e))

            competitor_events = sportybet_events + bet9ja_events
            competitor_duration_ms = int((time.perf_counter() - competitor_start_time) * 1000)

            # Log competitor completion
            if scrape_run_id:
                await self._log_phase_history(
                    db, scrape_run_id, None, ScrapePhase.COMPLETED,
                    f"Scraped {competitor_events} competitor events ({competitor_duration_ms}ms)",
                    events_count=competitor_events
                )

            progress = await self._emit_phase(
                db, scrape_run_id, None, ScrapePhase.COMPLETED,
                f"Scraped {competitor_events} competitor events ({competitor_duration_ms}ms)",
                events_count=competitor_events
            )
            progress.current = 2
            progress.total = total_phases
            progress.duration_ms = competitor_duration_ms
            yield progress

        except Exception as e:
            error_ctx = ScrapeErrorContext(
                error_type="unknown",
                error_message=str(e) or f"Unknown error: {type(e).__name__}",
                platform=None,
                recoverable=False,
            )
            logger.error("competitor_scrape_failed", error=str(e))

            if scrape_run_id:
                await db.rollback()
                await self._log_phase_history(
                    db, scrape_run_id, None, ScrapePhase.FAILED,
                    f"Competitors failed: {error_ctx.error_message}",
                    error=error_ctx
                )

            elapsed_ms = int((time.perf_counter() - competitor_start_time) * 1000)
            progress = await self._emit_phase(
                db, scrape_run_id, None, ScrapePhase.FAILED,
                f"Competitors failed: {error_ctx.error_message}",
                error=error_ctx
            )
            progress.current = 2
            progress.total = total_phases
            progress.elapsed_ms = elapsed_ms
            yield progress

        # Commit all changes
        await db.commit()

        # Log and yield final completion
        total_all = total_events + competitor_events
        logger.info("scrape_complete", total_events=total_all, betpawa=total_events, competitors=competitor_events)
        if scrape_run_id:
            await self._log_phase_history(
                db, scrape_run_id, None, ScrapePhase.COMPLETED,
                f"Scrape complete: {total_events} BetPawa + {competitor_events} competitors = {total_all} total",
                events_count=total_all
            )

        progress = await self._emit_phase(
            db, scrape_run_id, None, ScrapePhase.COMPLETED,
            f"Scrape complete: {total_events} BetPawa + {competitor_events} competitors = {total_all} total",
            events_count=total_all
        )
        progress.current = total_phases
        progress.total = total_phases
        yield progress

    def _create_error_context(
        self,
        e: Exception,
        platform: Platform,
        timeout: float,
    ) -> ScrapeErrorContext:
        """Create a structured error context from an exception."""
        if isinstance(e, (TimeoutError, asyncio.TimeoutError)):
            return ScrapeErrorContext(
                error_type="timeout",
                error_message=f"Platform scrape timed out after {timeout}s",
                platform=platform.value,
                recoverable=True,
            )
        elif "connection" in str(e).lower() or "network" in str(e).lower():
            return ScrapeErrorContext(
                error_type="network",
                error_message=str(e) or f"Network error: {type(e).__name__}",
                platform=platform.value,
                recoverable=True,
            )
        else:
            return ScrapeErrorContext(
                error_type="unknown",
                error_message=str(e) or f"Unknown error: {type(e).__name__}",
                platform=platform.value,
                recoverable=False,
            )

    async def _scrape_legacy_flow(
        self,
        platforms: list[Platform] | None,
        sport_id: str | None,
        competition_id: str | None,
        timeout: float,
        scrape_run_id: int | None,
        db: AsyncSession | None,
    ) -> AsyncGenerator[ScrapeProgress, None]:
        """Legacy scrape flow with sportradar_id filtering.

        Collects SportRadar IDs from BetPawa scrape and passes them to
        SportyBet/Bet9ja for precise event matching within the same session.

        Args:
            platforms: List of platforms to scrape (default: all).
            sport_id: Filter to specific sport.
            competition_id: Filter to specific competition.
            timeout: Per-platform timeout in seconds.
            scrape_run_id: Optional ScrapeRun ID.
            db: Optional database session.

        Yields:
            ScrapeProgress updates for each stage of scraping.
        """
        target_platforms = platforms or list(Platform)
        total = len(target_platforms)
        total_events = 0

        # Collect SportRadar IDs from BetPawa for cross-platform lookup
        betpawa_sportradar_ids: list[str] = []

        # Log and persist initializing phase
        logger.info("scrape_starting", platforms=[p.value for p in target_platforms], total=total)
        if db and scrape_run_id:
            await self._log_phase_history(
                db, scrape_run_id, None, ScrapePhase.INITIALIZING,
                f"Starting scrape of {total} platforms"
            )

        # Yield starting progress
        progress = await self._emit_phase(
            db, scrape_run_id, None, ScrapePhase.INITIALIZING,
            f"Starting scrape of {total} platforms"
        )
        progress.current = 0
        progress.total = total
        yield progress

        # Scrape each platform sequentially for progress updates
        for idx, platform in enumerate(target_platforms):
            platform_start_time = time.perf_counter()

            # Log and yield scraping phase
            logger.info("platform_scrape_start", platform=platform.value, index=idx)
            if db and scrape_run_id:
                await self._log_phase_history(
                    db, scrape_run_id, platform, ScrapePhase.SCRAPING,
                    f"Scraping {platform.value}..."
                )

            progress = await self._emit_phase(
                db, scrape_run_id, platform, ScrapePhase.SCRAPING,
                f"Scraping {platform.value}..."
            )
            progress.current = idx
            progress.total = total
            yield progress

            try:
                # Scrape this platform
                # Pass SportRadar IDs to competitor platforms (not to BetPawa itself)
                events, duration_ms = await self._scrape_platform(
                    platform, sport_id, competition_id, False, timeout, db,
                    sportradar_ids=betpawa_sportradar_ids if platform != Platform.BETPAWA else None,
                )

                # After BetPawa scrape, extract SportRadar IDs for competitor platforms
                if platform == Platform.BETPAWA:
                    betpawa_sportradar_ids = [
                        e["sportradar_id"] for e in events
                        if e.get("sportradar_id")
                    ]
                    logger.info(f"Collected {len(betpawa_sportradar_ids)} SportRadar IDs from BetPawa")

                logger.info("platform_scrape_complete", platform=platform.value, events_count=len(events), duration_ms=duration_ms)

                # Store events if DB session provided
                if db and events:
                    if db and scrape_run_id:
                        await self._log_phase_history(
                            db, scrape_run_id, platform, ScrapePhase.STORING,
                            f"Storing {len(events)} {platform.value} events...",
                            events_count=len(events)
                        )

                    progress = await self._emit_phase(
                        db, scrape_run_id, platform, ScrapePhase.STORING,
                        f"Storing {len(events)} {platform.value} events...",
                        events_count=len(events)
                    )
                    progress.current = idx
                    progress.total = total
                    yield progress

                    try:
                        await self._store_events(db, platform, events)
                    except Exception as e:
                        error_ctx = ScrapeErrorContext(
                            error_type="storage",
                            error_message=str(e),
                            platform=platform.value,
                            recoverable=False,
                        )
                        logger.error("storage_failed", platform=platform.value, error=str(e), exc_info=True)
                        if scrape_run_id and db:
                            await db.rollback()
                            await self._log_error(db, scrape_run_id, platform, e)

                total_events += len(events)

                # Log and yield completed phase for this platform
                if db and scrape_run_id:
                    await self._log_phase_history(
                        db, scrape_run_id, platform, ScrapePhase.COMPLETED,
                        f"Scraped {len(events)} events from {platform.value} ({duration_ms}ms)",
                        events_count=len(events)
                    )

                progress = await self._emit_phase(
                    db, scrape_run_id, platform, ScrapePhase.COMPLETED,
                    f"Scraped {len(events)} events from {platform.value} ({duration_ms}ms)",
                    events_count=len(events)
                )
                progress.current = idx + 1
                progress.total = total
                progress.duration_ms = duration_ms
                yield progress

            except Exception as e:
                # Create structured error context
                error_ctx = self._create_error_context(e, platform, timeout)
                logger.error("platform_scrape_failed", platform=platform.value, error_type=error_ctx.error_type, error_message=error_ctx.error_message)

                # Log error to DB
                if db and scrape_run_id:
                    await db.rollback()
                    await self._log_error(db, scrape_run_id, platform, e)
                    await self._log_phase_history(
                        db, scrape_run_id, platform, ScrapePhase.FAILED,
                        f"Failed: {error_ctx.error_message}",
                        error=error_ctx
                    )

                elapsed_ms = int((time.perf_counter() - platform_start_time) * 1000)
                progress = await self._emit_phase(
                    db, scrape_run_id, platform, ScrapePhase.FAILED,
                    f"Failed: {error_ctx.error_message}",
                    error=error_ctx
                )
                progress.current = idx + 1
                progress.total = total
                progress.elapsed_ms = elapsed_ms
                yield progress

        # Commit all changes
        if db:
            await db.commit()

        # Log and yield final completion progress
        logger.info("scrape_complete", total_events=total_events, platforms=total)
        if db and scrape_run_id:
            await self._log_phase_history(
                db, scrape_run_id, None, ScrapePhase.COMPLETED,
                f"Scrape complete: {total_events} total events from {total} platforms",
                events_count=total_events
            )

        progress = await self._emit_phase(
            db, scrape_run_id, None, ScrapePhase.COMPLETED,
            f"Scrape complete: {total_events} total events from {total} platforms",
            events_count=total_events
        )
        progress.current = total
        progress.total = total
        yield progress

    async def _scrape_platform(
        self,
        platform: Platform,
        sport_id: str | None,
        competition_id: str | None,
        include_data: bool,
        timeout: float,
        db: AsyncSession | None = None,
        sportradar_ids: list[str] | None = None,
    ) -> tuple[list[dict], int]:
        """Scrape a single platform with timeout.

        Args:
            platform: Platform to scrape.
            sport_id: Filter to specific sport (e.g., "2" for football).
            competition_id: Filter to specific competition.
            include_data: Whether to return event data.
            timeout: Timeout in seconds.
            db: Optional database session (required for SportyBet/Bet9ja).
            sportradar_ids: Optional list of SportRadar IDs to fetch (from BetPawa).
                Used by competitor platforms for precise event matching.

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
                return await self._scrape_sportybet(client, db, sportradar_ids)
            elif platform == Platform.BET9JA:
                if db is None:
                    logger.warning(
                        "Bet9ja scraping requires database session - skipping"
                    )
                    return []
                return await self._scrape_bet9ja(client, db, sportradar_ids)
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

        Uses parallel fetching across competitions with semaphore to limit
        concurrent requests. This provides ~10x speedup vs sequential scraping.

        Args:
            client: BetPawa API client.
            competition_id: Optional specific competition ID to scrape.

        Returns:
            List of event dicts in standard format for EventMatchingService.
        """
        if competition_id:
            # Scrape specific competition
            competitions_to_scrape = [competition_id]
        else:
            # Discover all football competitions
            competitions_to_scrape = await self._get_betpawa_competitions(client)

        logger.info(
            f"Scraping {len(competitions_to_scrape)} BetPawa competitions in parallel"
        )

        # Use semaphore to limit concurrent competition requests (5 concurrent)
        # Keep low since each competition spawns ~15 parallel event fetches (5×15=75 max concurrent)
        semaphore = asyncio.Semaphore(5)

        async def scrape_competition(comp_id: str) -> list[dict]:
            """Scrape a single competition with rate limiting."""
            async with semaphore:
                try:
                    return await self._scrape_betpawa_competition(client, comp_id)
                except Exception as e:
                    logger.warning(
                        f"Failed to scrape BetPawa competition {comp_id}: {e}"
                    )
                    return []

        # Scrape all competitions in parallel (limited by semaphore)
        results = await asyncio.gather(
            *[scrape_competition(comp_id) for comp_id in competitions_to_scrape],
            return_exceptions=True,
        )

        # Flatten results, filtering out exceptions
        events: list[dict] = []
        for result in results:
            if isinstance(result, list):
                events.extend(result)
            # Exceptions already logged in scrape_competition

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
        (including markets) for each event using parallel requests.

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

        responses = events_response.get("responses", [])

        if not responses:
            return []

        first_response = responses[0]
        events_data = first_response.get("responses", [])

        # Parse all events first
        parsed_events = []
        for event_data in events_data:
            parsed = self._parse_betpawa_event(event_data)
            if parsed:
                parsed_events.append(parsed)

        if not parsed_events:
            return []

        # Use semaphore to limit concurrent requests (30 parallel with 100 connection pool)
        semaphore = asyncio.Semaphore(30)

        async def fetch_single(parsed: dict) -> dict | None:
            """Fetch single event with rate limiting."""
            async with semaphore:
                event_id = parsed["external_event_id"]
                try:
                    full_event_data = await client.fetch_event(event_id)
                    parsed["raw_data"] = full_event_data
                    return parsed
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch full BetPawa event {event_id}: {e}"
                    )
                    # Still include event without raw_data
                    return parsed

        # Fetch all events in parallel (limited by semaphore)
        results = await asyncio.gather(
            *[fetch_single(parsed) for parsed in parsed_events],
            return_exceptions=True,
        )

        # Filter out None results and exceptions
        events = [r for r in results if r is not None and not isinstance(r, Exception)]

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
        sportradar_ids: list[str] | None = None,
    ) -> list[dict]:
        """Scrape events from SportyBet via SportRadar ID lookup.

        If sportradar_ids provided, uses those directly (from current BetPawa scrape).
        Otherwise, queries database for upcoming events (fallback for non-streaming scrape).

        Args:
            client: SportyBet API client.
            db: Async database session for event lookup.
            sportradar_ids: Optional list of SportRadar IDs from current BetPawa session.

        Returns:
            List of event dicts with raw_data for OddsSnapshot storage.
        """
        # Use provided IDs if available, otherwise query DB (fallback)
        if sportradar_ids:
            ids_to_fetch = sportradar_ids
            logger.info(f"Using {len(ids_to_fetch)} fresh SportRadar IDs from BetPawa session")

            # Need to look up Event objects for the IDs we're fetching
            result = await db.execute(
                select(Event).where(
                    Event.sportradar_id.in_(ids_to_fetch),
                )
            )
            db_events = result.scalars().all()
            events_by_id = {e.sportradar_id: e for e in db_events}
        else:
            # Fallback: query DB for existing events (used by scrape_all, not scrape_with_progress)
            result = await db.execute(
                select(Event).where(
                    Event.sportradar_id.isnot(None),
                    Event.kickoff > datetime.now(timezone.utc).replace(tzinfo=None),
                )
            )
            db_events = result.scalars().all()
            ids_to_fetch = [e.sportradar_id for e in db_events]
            events_by_id = {e.sportradar_id: e for e in db_events}
            logger.info(f"Using {len(ids_to_fetch)} SportRadar IDs from database")

        if not ids_to_fetch:
            return []

        logger.info(
            f"Fetching {len(ids_to_fetch)} events from SportyBet"
        )

        # Use semaphore to limit concurrent requests (30 parallel with 100 connection pool)
        semaphore = asyncio.Semaphore(30)

        async def fetch_single(sportradar_id: str) -> dict | None:
            """Fetch single event with rate limiting."""
            async with semaphore:
                sportybet_id = f"sr:match:{sportradar_id}"
                try:
                    raw_data = await client.fetch_event(sportybet_id)
                    event = events_by_id.get(sportradar_id)
                    return {
                        "sportradar_id": sportradar_id,
                        "external_event_id": sportybet_id,
                        "event_url": f"https://www.sportybet.com/ng/sport/match/{sportybet_id}",
                        "raw_data": raw_data,
                        "event": event,  # May be None if not yet stored
                    }
                except InvalidEventIdError:
                    logger.debug(
                        f"Event {sportradar_id} not found on SportyBet"
                    )
                    return None
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch event {sportradar_id} from SportyBet: {e}"
                    )
                    return None

        # Fetch all events in parallel (limited by semaphore)
        results = await asyncio.gather(
            *[fetch_single(sr_id) for sr_id in ids_to_fetch],
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
        sportradar_ids: list[str] | None = None,
    ) -> list[dict]:
        """Scrape events from Bet9ja via tournament discovery.

        Discovers football tournaments and fetches events from each
        in parallel using asyncio.gather with semaphore, matching via
        EXTID (SportRadar ID) field.

        If sportradar_ids provided, filters results to only include events
        matching those IDs (from current BetPawa session).

        Args:
            client: Bet9ja API client.
            db: Async database session (used for event matching).
            sportradar_ids: Optional list of SportRadar IDs from current BetPawa session.

        Returns:
            List of event dicts in standard format for EventMatchingService.
        """
        # Discover football tournaments
        try:
            sports_data = await client.fetch_sports()
            tournament_ids = self._extract_football_tournaments(sports_data)
        except Exception as e:
            logger.error(f"Failed to fetch Bet9ja sports structure: {e}")
            return []

        logger.info(
            f"Scraping {len(tournament_ids)} Bet9ja football tournaments in parallel"
        )

        # Use semaphore to limit concurrent tournament requests (10 concurrent)
        semaphore = asyncio.Semaphore(10)

        async def scrape_tournament(tournament_id: str) -> list[dict]:
            """Scrape a single tournament with rate limiting."""
            async with semaphore:
                try:
                    tournament_events = await client.fetch_events(tournament_id)

                    parsed_events = []
                    for event_data in tournament_events:
                        parsed = self._parse_bet9ja_event(event_data, tournament_id)
                        if parsed:
                            parsed_events.append(parsed)

                    return parsed_events
                except Exception as e:
                    logger.warning(
                        f"Failed to scrape Bet9ja tournament {tournament_id}: {e}"
                    )
                    return []
                finally:
                    # Small delay after each request for rate limiting
                    await asyncio.sleep(0.05)

        # Scrape all tournaments in parallel (limited by semaphore)
        results = await asyncio.gather(
            *[scrape_tournament(tid) for tid in tournament_ids],
            return_exceptions=True,
        )

        # Flatten results, filtering out exceptions
        events: list[dict] = []
        for result in results:
            if isinstance(result, list):
                events.extend(result)
            # Exceptions already logged in scrape_tournament

        # Filter to only events matching provided SportRadar IDs (if given)
        if sportradar_ids:
            sportradar_set = set(sportradar_ids)
            original_count = len(events)
            events = [e for e in events if e.get("sportradar_id") in sportradar_set]
            logger.info(f"Filtered Bet9ja events from {original_count} to {len(events)} matching BetPawa session")
        else:
            logger.info(f"Scraped {len(events)} events from Bet9ja (no filter)")

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
            # But with fresh SportRadar IDs, event reference may be None
            markets_count = 0
            skipped_count = 0
            for event_data in events:
                event = event_data.get("event")  # DB event reference (may be None)

                if event is None:
                    # Event not in DB yet - try to look it up by sportradar_id
                    sportradar_id = event_data.get("sportradar_id")
                    if sportradar_id:
                        result = await db.execute(
                            select(Event).where(Event.sportradar_id == sportradar_id)
                        )
                        event = result.scalar_one_or_none()

                    if event is None:
                        # Still no event - skip (BetPawa storage hasn't completed yet)
                        skipped_count += 1
                        continue

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

            stored_count = len(events) - skipped_count
            logger.info(
                f"Stored {stored_count} event links and {markets_count} markets for {platform}"
                + (f" (skipped {skipped_count} not yet in DB)" if skipped_count else "")
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
