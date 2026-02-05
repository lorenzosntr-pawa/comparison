"""Scheduled job functions for periodic scraping and cleanup."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select

from src.db.engine import async_session_factory
from src.db.models.scrape import ScrapeRun, ScrapeStatus
from src.db.models.settings import Settings
from src.scraping.broadcaster import progress_registry
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.event_coordinator import EventCoordinator
from src.scraping.schemas import Platform, ScrapeProgress
from src.scraping.tournament_discovery import TournamentDiscoveryService

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

            # Run tournament discovery to pick up any new tournaments
            discovery_service = TournamentDiscoveryService()
            discovery_results = await discovery_service.discover_all(
                sportybet_client, bet9ja_client, db
            )
            logger.info(
                f"Tournament discovery: sportybet new={discovery_results['sportybet']['new']}, "
                f"bet9ja new={discovery_results['bet9ja']['new']}"
            )

            # Create EventCoordinator from settings (with optional cache and write queue)
            coordinator = EventCoordinator.from_settings(
                betpawa_client=betpawa_client,
                sportybet_client=sportybet_client,
                bet9ja_client=bet9ja_client,
                settings=settings,
                odds_cache=getattr(_app_state, "odds_cache", None),
                write_queue=getattr(_app_state, "write_queue", None),
            )

            # Execute scrape with progress streaming
            platform_timings: dict[str, dict] = {}
            total_events = 0
            failed_count = 0
            final_status = ScrapeStatus.COMPLETED

            async for progress_event in coordinator.run_full_cycle(
                db=db,
                scrape_run_id=scrape_run_id,
            ):
                # Convert dict events to ScrapeProgress for broadcaster compatibility
                event_type = progress_event.get("event_type", "")

                if event_type == "CYCLE_START":
                    await broadcaster.publish(ScrapeProgress(
                        platform=None,
                        phase="starting",
                        current=0,
                        total=3,
                        message="Starting event-centric scrape cycle",
                    ))
                elif event_type == "DISCOVERY_COMPLETE":
                    total = progress_event.get("total_events", 0)
                    await broadcaster.publish(ScrapeProgress(
                        platform=None,
                        phase="discovery",
                        current=1,
                        total=3,
                        message=f"Discovered {total} events across all platforms",
                        events_count=total,
                    ))
                elif event_type == "BATCH_COMPLETE":
                    processed = progress_event.get("events_stored", 0)
                    await broadcaster.publish(ScrapeProgress(
                        platform=None,
                        phase="scraping",
                        current=2,
                        total=3,
                        message=f"Processed batch: {processed} events stored",
                        events_count=processed,
                    ))
                elif event_type == "CYCLE_COMPLETE":
                    total_events = progress_event.get("events_scraped", 0)
                    failed_count = progress_event.get("events_failed", 0)
                    total_ms = progress_event.get("total_timing_ms", 0)

                    await broadcaster.publish(ScrapeProgress(
                        platform=None,
                        phase="completed",
                        current=3,
                        total=3,
                        message=f"Completed: {total_events} events scraped ({total_ms}ms)",
                        events_count=total_events,
                        duration_ms=total_ms,
                    ))

                    # Determine final status
                    if failed_count > 0 and total_events > 0:
                        final_status = ScrapeStatus.PARTIAL
                    elif total_events == 0:
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

            # Evict expired events from cache (2 hours past kickoff grace period)
            odds_cache = getattr(_app_state, "odds_cache", None)
            if odds_cache:
                cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
                evicted = odds_cache.evict_expired(cutoff)
                if evicted > 0:
                    logger.info(
                        f"Cache eviction: {evicted} events removed, "
                        f"stats={odds_cache.stats()}"
                    )

            # Log write queue stats after scrape cycle
            write_queue = getattr(_app_state, "write_queue", None)
            if write_queue:
                stats = write_queue.stats()
                logger.info(
                    f"Write queue post-scrape: "
                    f"queue_size={stats['queue_size']}, "
                    f"queue_maxsize={stats['queue_maxsize']}, "
                    f"running={stats['running']}"
                )

        except Exception as e:
            logger.exception(f"ScrapeRun {scrape_run_id} failed: {e}")

            # Publish failure to broadcaster (uses module-level ScrapeProgress import)
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
