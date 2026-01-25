"""APScheduler configuration and lifecycle management."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.db.models.settings import Settings

logger = logging.getLogger(__name__)

# Module-level scheduler instance with UTC timezone
scheduler = AsyncIOScheduler(timezone="UTC")

# Default interval used during startup before DB is available
DEFAULT_INTERVAL_MINUTES = 5


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
    """Configure the scheduler with scraping jobs.

    Adds the scrape_all_platforms job with default interval.
    Uses deferred import to avoid circular dependencies.

    Note: Uses default interval on startup. Call update_scheduler_interval()
    after DB is available to sync with stored settings.
    """
    # Deferred import to avoid circular dependency
    from src.scheduling.jobs import scrape_all_platforms

    # Use default interval on startup - will be updated when settings are loaded
    scheduler.add_job(
        scrape_all_platforms,
        trigger=IntervalTrigger(minutes=DEFAULT_INTERVAL_MINUTES),
        id="scrape_all_platforms",
        replace_existing=True,
        misfire_grace_time=60,
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
    """Sync scheduler interval from database settings.

    Fetches stored settings and updates scheduler interval if different from default.
    Called during app lifespan after scheduler is started.
    """
    settings = await get_settings_from_db()

    if settings is None:
        logger.info(f"Using default interval: {DEFAULT_INTERVAL_MINUTES} minutes")
        return

    stored_interval = settings.scrape_interval_minutes
    if stored_interval != DEFAULT_INTERVAL_MINUTES:
        update_scheduler_interval(stored_interval)
        logger.info(f"Synced scheduler interval from settings: {stored_interval} minutes")
    else:
        logger.info(f"Settings match default interval: {DEFAULT_INTERVAL_MINUTES} minutes")
