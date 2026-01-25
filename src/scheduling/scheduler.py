"""APScheduler configuration and lifecycle management."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.db.models.settings import Settings

logger = logging.getLogger(__name__)

# Module-level scheduler instance with UTC timezone
scheduler = AsyncIOScheduler(timezone="UTC")

# Default intervals used during startup before DB is available
DEFAULT_INTERVAL_MINUTES = 5
DEFAULT_CLEANUP_HOURS = 24


async def get_settings_from_db() -> Settings | None:
    """Fetch settings from database.

    Returns:
        Settings object or None if not found.
    """
    from sqlalchemy import select

    from src.db.engine import async_session_factory

    try:
        async with async_session_factory() as session:
            result = await session.execute(select(Settings).where(Settings.id == 1))
            return result.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"Failed to fetch settings from database: {e}")
        return None


def configure_scheduler() -> None:
    """Configure the scheduler with scraping and cleanup jobs.

    Adds the scrape_all_platforms and cleanup_old_data jobs with default intervals.
    Uses deferred import to avoid circular dependencies.

    Note: Uses default intervals on startup. Call sync_settings_on_startup()
    after DB is available to sync with stored settings.
    """
    # Deferred import to avoid circular dependency
    from src.scheduling.jobs import cleanup_old_data, scrape_all_platforms

    # Use default interval on startup - will be updated when settings are loaded
    scheduler.add_job(
        scrape_all_platforms,
        trigger=IntervalTrigger(minutes=DEFAULT_INTERVAL_MINUTES),
        id="scrape_all_platforms",
        replace_existing=True,
        misfire_grace_time=60,
        coalesce=True,
    )

    # Add cleanup job with default 24-hour interval
    scheduler.add_job(
        cleanup_old_data,
        trigger=IntervalTrigger(hours=DEFAULT_CLEANUP_HOURS),
        id="cleanup_old_data",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hour grace for cleanup
        coalesce=True,
    )


def update_scheduler_interval(interval_minutes: int) -> None:
    """Update the scheduler job interval at runtime.

    Reschedules the scrape_all_platforms job with the new interval.

    Args:
        interval_minutes: New interval in minutes.
    """
    job = scheduler.get_job("scrape_all_platforms")
    if job:
        scheduler.reschedule_job(
            "scrape_all_platforms",
            trigger=IntervalTrigger(minutes=interval_minutes),
        )
        logger.info(f"Rescheduled scrape job with interval: {interval_minutes} minutes")


def update_cleanup_interval(hours: int) -> None:
    """Update the cleanup job interval at runtime.

    Reschedules the cleanup_old_data job with the new interval.

    Args:
        hours: New interval in hours.
    """
    job = scheduler.get_job("cleanup_old_data")
    if job:
        scheduler.reschedule_job(
            "cleanup_old_data",
            trigger=IntervalTrigger(hours=hours),
        )
        logger.info(f"Rescheduled cleanup job with interval: {hours} hours")


def start_scheduler() -> None:
    """Start the scheduler if not already running."""
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler(wait: bool = True) -> None:
    """Shutdown the scheduler gracefully.

    Args:
        wait: If True, wait for running jobs to complete before returning.
    """
    if scheduler.running:
        scheduler.shutdown(wait=wait)


async def sync_settings_on_startup() -> None:
    """Sync scheduler intervals from database settings.

    Fetches stored settings and updates scheduler intervals if different from defaults.
    Called during app lifespan after scheduler is started.
    """
    settings = await get_settings_from_db()

    if settings is None:
        logger.info(
            f"Using default intervals: scrape={DEFAULT_INTERVAL_MINUTES}min, "
            f"cleanup={DEFAULT_CLEANUP_HOURS}h"
        )
        return

    # Sync scrape interval
    stored_interval = settings.scrape_interval_minutes
    if stored_interval != DEFAULT_INTERVAL_MINUTES:
        update_scheduler_interval(stored_interval)
        logger.info(f"Synced scrape interval from settings: {stored_interval} minutes")
    else:
        logger.info(f"Scrape interval matches default: {DEFAULT_INTERVAL_MINUTES} minutes")

    # Sync cleanup interval
    stored_cleanup_hours = settings.cleanup_frequency_hours
    if stored_cleanup_hours != DEFAULT_CLEANUP_HOURS:
        update_cleanup_interval(stored_cleanup_hours)
        logger.info(f"Synced cleanup interval from settings: {stored_cleanup_hours} hours")
    else:
        logger.info(f"Cleanup interval matches default: {DEFAULT_CLEANUP_HOURS} hours")
