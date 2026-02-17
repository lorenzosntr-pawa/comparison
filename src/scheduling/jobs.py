"""Scheduled job functions for periodic scraping and cleanup.

This module contains the async job functions invoked by APScheduler:

Jobs:
    scrape_all_platforms(): Main scraping job (default: every 5 minutes)
    cleanup_old_data(): Data retention cleanup (default: every 24 hours)

Integration:
    Jobs access app.state via set_app_state() called during lifespan.
    This provides HTTP clients, OddsCache, and AsyncWriteQueue.

Coordination:
    is_scraping_active() allows cleanup to check if scraping is in progress
    and skip to avoid conflicts (cleanup deletes while scrape inserts).

Scrape Job Flow:
    1. Create ScrapeRun record with RUNNING status
    2. Create ProgressBroadcaster for SSE streaming
    3. Run TournamentDiscoveryService.discover_all()
    4. Create EventCoordinator.from_settings()
    5. Execute coordinator.run_full_cycle(), publish progress
    6. Update ScrapeRun with results, evict expired cache entries
    7. Clean up broadcaster

APScheduler Configuration:
    Jobs are configured in src/scheduling/scheduler.py with IntervalTrigger.
    Intervals can be updated at runtime via update_scheduler_interval().
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import delete, func, select, text

from src.db.engine import async_session_factory
from src.db.models.scrape import ScrapeRun, ScrapeStatus
from src.db.models.settings import Settings
from src.db.models.storage_alert import StorageAlert
from src.db.models.storage_sample import StorageSample
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


async def sample_storage_sizes() -> None:
    """Scheduled job to sample database storage sizes.

    Queries PostgreSQL system tables for current storage sizes,
    creates a StorageSample record, checks for abnormal growth,
    and prunes old samples and resolved alerts.
    Runs daily at 3 AM UTC (after cleanup at 2 AM).
    """
    log = structlog.get_logger("src.scheduling.jobs.storage")
    log.info("storage.sampling.start")

    # Growth alert thresholds
    GROWTH_WARNING_PERCENT = 20  # 20% growth in 24h triggers warning
    SIZE_CRITICAL_BYTES = 50 * 1024**3  # 50 GB triggers critical alert

    try:
        async with async_session_factory() as session:
            # Query table sizes from pg_stat_user_tables
            table_sizes_query = text("""
                SELECT
                    relname as table_name,
                    pg_total_relation_size(quote_ident(relname)) as size_bytes
                FROM pg_stat_user_tables
            """)
            result = await session.execute(table_sizes_query)
            rows = result.fetchall()

            table_sizes_dict = {row.table_name: row.size_bytes for row in rows}

            # Query total database size
            total_size_query = text("""
                SELECT pg_database_size(current_database()) as total_bytes
            """)
            total_result = await session.execute(total_size_query)
            total_row = total_result.fetchone()
            total_bytes = total_row.total_bytes

            # Create StorageSample record
            sample = StorageSample(
                total_bytes=total_bytes,
                table_sizes=table_sizes_dict,
            )
            session.add(sample)
            await session.commit()
            await session.refresh(sample)

            log.info(
                "storage.sampling.recorded",
                sample_id=sample.id,
                total_bytes=total_bytes,
                table_count=len(table_sizes_dict),
            )

            # Check for growth alerts - query previous sample
            prev_result = await session.execute(
                select(StorageSample)
                .where(StorageSample.id < sample.id)
                .order_by(StorageSample.sampled_at.desc())
                .limit(1)
            )
            prev_sample = prev_result.scalar_one_or_none()

            if prev_sample and prev_sample.total_bytes > 0:
                # Calculate growth percentage
                growth_bytes = total_bytes - prev_sample.total_bytes
                growth_percent = (growth_bytes / prev_sample.total_bytes) * 100

                # Check for growth warning
                if growth_percent > GROWTH_WARNING_PERCENT:
                    alert = StorageAlert(
                        alert_type="growth_warning",
                        message=f"Database grew {growth_percent:.1f}% since last sample ({_format_bytes(prev_sample.total_bytes)} → {_format_bytes(total_bytes)})",
                        current_bytes=total_bytes,
                        previous_bytes=prev_sample.total_bytes,
                        growth_percent=growth_percent,
                    )
                    session.add(alert)
                    await session.commit()

                    log.warning(
                        "storage.alert.growth_warning",
                        alert_id=alert.id,
                        growth_percent=growth_percent,
                        current_bytes=total_bytes,
                        previous_bytes=prev_sample.total_bytes,
                    )

            # Check for critical size alert
            if total_bytes > SIZE_CRITICAL_BYTES:
                # Check if we already have an active critical alert
                existing = await session.execute(
                    select(StorageAlert)
                    .where(StorageAlert.alert_type == "size_critical")
                    .where(StorageAlert.resolved_at.is_(None))
                    .limit(1)
                )
                if not existing.scalar_one_or_none():
                    alert = StorageAlert(
                        alert_type="size_critical",
                        message=f"Database size ({_format_bytes(total_bytes)}) exceeds 50 GB threshold",
                        current_bytes=total_bytes,
                        previous_bytes=prev_sample.total_bytes if prev_sample else 0,
                        growth_percent=0,
                    )
                    session.add(alert)
                    await session.commit()

                    log.warning(
                        "storage.alert.size_critical",
                        alert_id=alert.id,
                        total_bytes=total_bytes,
                    )

            # Prune old samples (keep last 90)
            subquery = (
                select(StorageSample.sampled_at)
                .order_by(StorageSample.sampled_at.desc())
                .offset(90)
                .limit(1)
                .scalar_subquery()
            )

            delete_stmt = delete(StorageSample).where(
                StorageSample.sampled_at < subquery
            )
            delete_result = await session.execute(delete_stmt)
            deleted_count = delete_result.rowcount
            await session.commit()

            if deleted_count > 0:
                log.info(
                    "storage.sampling.pruned",
                    deleted_count=deleted_count,
                )

            # Prune old resolved alerts (keep last 30)
            alert_subquery = (
                select(StorageAlert.created_at)
                .where(StorageAlert.resolved_at.is_not(None))
                .order_by(StorageAlert.created_at.desc())
                .offset(30)
                .limit(1)
                .scalar_subquery()
            )

            alert_delete_stmt = delete(StorageAlert).where(
                StorageAlert.resolved_at.is_not(None),
                StorageAlert.created_at < alert_subquery,
            )
            alert_delete_result = await session.execute(alert_delete_stmt)
            alerts_deleted = alert_delete_result.rowcount
            await session.commit()

            if alerts_deleted > 0:
                log.info(
                    "storage.alerts.pruned",
                    deleted_count=alerts_deleted,
                )

    except Exception as e:
        log.exception("storage.sampling.failed", error=str(e))


def _format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    if bytes_value == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    k = 1024
    i = 0
    while bytes_value >= k and i < len(units) - 1:
        bytes_value /= k
        i += 1
    return f"{bytes_value:.2f} {units[i]}"
