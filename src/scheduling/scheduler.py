"""APScheduler configuration and lifecycle management."""

import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Module-level scheduler instance with UTC timezone
scheduler = AsyncIOScheduler(timezone="UTC")


def configure_scheduler() -> None:
    """Configure the scheduler with scraping jobs.

    Adds the scrape_all_platforms job with configurable interval.
    Uses deferred import to avoid circular dependencies.
    """
    # Deferred import to avoid circular dependency
    from src.scheduling.jobs import scrape_all_platforms

    interval_minutes = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "5"))

    scheduler.add_job(
        scrape_all_platforms,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="scrape_all_platforms",
        replace_existing=True,
        misfire_grace_time=60,
        coalesce=True,
    )


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
