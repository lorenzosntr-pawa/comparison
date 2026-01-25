"""Scheduled job functions for periodic scraping and cleanup."""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from src.db.engine import async_session_factory
from src.db.models.scrape import ScrapeRun, ScrapeStatus
from src.db.models.settings import Settings
from src.scraping.broadcaster import progress_registry
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.competitor_events import CompetitorEventScrapingService
from src.scraping.orchestrator import ScrapingOrchestrator
from src.scraping.schemas import Platform

logger = logging.getLogger(__name__)

# Module-level reference to app.state, set during lifespan startup
_app_state: Any = None

# Scraping activity tracking for coordination with cleanup
_scraping_active: bool = False


def is_scraping_active() -> bool:
    """Check if scraping is currently in progress.

    Returns:
        True if a scraping job is currently running.
    """
    return _scraping_active


def set_app_state(state: Any) -> None:
    """Set the app state reference for job access to HTTP clients.

    Args:
        state: FastAPI app.state object containing HTTP clients.
    """
    global _app_state
    _app_state = state


async def scrape_all_platforms() -> None:
    """Scheduled job to scrape all platforms.

    Creates a ScrapeRun record, executes scraping via orchestrator with
    progress streaming, and updates the record with results or failure status.

    Progress is published to a broadcaster so UI can observe via SSE.
    Respects enabled_platforms from settings to filter which platforms to scrape.
    """
    global _scraping_active
    logger.info("Starting scheduled scrape job")

    if _app_state is None:
        logger.error("App state not initialized - cannot run scheduled scrape")
        return

    async with async_session_factory() as db:
        # Fetch settings to get enabled platforms
        result = await db.execute(select(Settings).where(Settings.id == 1))
        settings = result.scalar_one_or_none()

        # Determine which platforms to scrape
        enabled_platforms: list[Platform] | None = None
        if settings and settings.enabled_platforms:
            # Map slug strings to Platform enum values
            slug_to_platform = {
                "sportybet": Platform.SPORTYBET,
                "betpawa": Platform.BETPAWA,
                "bet9ja": Platform.BET9JA,
            }
            enabled_platforms = [
                slug_to_platform[slug]
                for slug in settings.enabled_platforms
                if slug in slug_to_platform
            ]
            logger.info(f"Enabled platforms from settings: {[p.value for p in enabled_platforms]}")

            if not enabled_platforms:
                logger.warning("No platforms enabled in settings - skipping scrape")
                return

        # Create ScrapeRun record
        scrape_run = ScrapeRun(
            status=ScrapeStatus.RUNNING,
            trigger="scheduled",
        )
        db.add(scrape_run)
        await db.commit()
        await db.refresh(scrape_run)
        scrape_run_id = scrape_run.id

        logger.info(f"Created ScrapeRun {scrape_run_id}")

        # Create broadcaster for this scrape run
        broadcaster = progress_registry.create_broadcaster(scrape_run_id)

        # Mark scraping as active
        _scraping_active = True

        try:
            # Create clients from app state
            sportybet_client = SportyBetClient(_app_state.sportybet_client)
            betpawa_client = BetPawaClient(_app_state.betpawa_client)
            bet9ja_client = Bet9jaClient(_app_state.bet9ja_client)

            # Create competitor service for full-palimpsest scraping
            competitor_service = CompetitorEventScrapingService(
                sportybet_client, bet9ja_client
            )

            # Create orchestrator with competitor service for parallel scraping
            orchestrator = ScrapingOrchestrator(
                sportybet_client=sportybet_client,
                betpawa_client=betpawa_client,
                bet9ja_client=bet9ja_client,
                competitor_service=competitor_service,
            )

            # Execute scrape with progress streaming
            # scrape_with_progress yields progress updates sequentially
            platform_timings: dict[str, dict] = {}
            total_events = 0
            failed_count = 0
            final_status = ScrapeStatus.COMPLETED

            async for progress in orchestrator.scrape_with_progress(
                platforms=enabled_platforms,
                timeout=300.0,
                scrape_run_id=scrape_run_id,
                db=db,
            ):
                # Publish progress to broadcaster for SSE observers
                await broadcaster.publish(progress)

                # Track metrics from progress events
                if progress.platform and progress.phase == "completed":
                    # Platform completed successfully - store timing data
                    platform_timings[progress.platform.value] = {
                        "duration_ms": progress.duration_ms or 0,
                        "events_count": progress.events_count or 0,
                    }
                    total_events += progress.events_count or 0
                elif progress.platform and progress.phase == "failed":
                    # Platform failed
                    failed_count += 1

                # Check final status (overall completion event has platform=None)
                if progress.platform is None and progress.phase in ("completed", "failed"):
                    if progress.phase == "failed":
                        final_status = ScrapeStatus.FAILED
                    elif failed_count > 0 and len(platform_timings) > 0:
                        final_status = ScrapeStatus.PARTIAL
                    elif failed_count > 0:
                        final_status = ScrapeStatus.FAILED

            scrape_run.status = final_status
            scrape_run.events_scraped = total_events
            scrape_run.events_failed = failed_count
            scrape_run.platform_timings = platform_timings if platform_timings else None
            scrape_run.completed_at = datetime.utcnow()

            await db.commit()

            logger.info(
                f"Completed ScrapeRun {scrape_run_id}: "
                f"status={scrape_run.status.value}, events={total_events}"
            )

        except Exception as e:
            logger.exception(f"ScrapeRun {scrape_run_id} failed: {e}")

            # Publish failure to broadcaster
            from src.scraping.schemas import ScrapeProgress
            await broadcaster.publish(ScrapeProgress(
                platform=None,
                phase="failed",
                current=0,
                total=3,
                message=f"Scrape failed: {str(e)}",
            ))

            # Update ScrapeRun to FAILED status
            scrape_run.status = ScrapeStatus.FAILED
            scrape_run.completed_at = datetime.utcnow()
            await db.commit()

        finally:
            # Mark scraping as inactive
            _scraping_active = False

            # Close broadcaster and remove from registry
            await broadcaster.close()
            progress_registry.remove_broadcaster(scrape_run_id)


async def cleanup_old_data() -> None:
    """Scheduled job to clean up old data based on retention settings.

    Checks if scraping is in progress and skips if so to avoid conflicts.
    Uses settings from database for retention periods.
    Records cleanup run in cleanup_runs table.
    """
    logger.info("Starting scheduled cleanup job")

    # Skip if scraping is in progress
    if is_scraping_active():
        logger.info("Cleanup skipped - scraping is in progress")
        return

    async with async_session_factory() as session:
        # Get current retention settings
        result = await session.execute(select(Settings).where(Settings.id == 1))
        settings = result.scalar_one_or_none()

        if settings is None:
            logger.warning("No settings found - using default retention (30 days)")
            odds_days = 30
            match_days = 30
        else:
            odds_days = settings.odds_retention_days
            match_days = settings.match_retention_days

        # Execute cleanup with tracking
        from src.services.cleanup import execute_cleanup_with_tracking

        try:
            cleanup_run, result = await execute_cleanup_with_tracking(
                session=session,
                odds_days=odds_days,
                match_days=match_days,
                trigger="scheduled",
            )

            logger.info(
                f"Cleanup completed: cleanup_run_id={cleanup_run.id}, "
                f"odds_deleted={result.odds_deleted}, "
                f"events_deleted={result.events_deleted}, "
                f"tournaments_deleted={result.tournaments_deleted}, "
                f"duration={result.duration_seconds}s"
            )
        except Exception as e:
            logger.exception(f"Cleanup failed: {e}")
