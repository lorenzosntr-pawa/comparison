"""Scheduled job functions for periodic scraping."""

import logging
from datetime import datetime, timezone
from typing import Any

from src.db.engine import async_session_factory
from src.db.models.scrape import ScrapeRun, ScrapeStatus
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.orchestrator import ScrapingOrchestrator

logger = logging.getLogger(__name__)

# Module-level reference to app.state, set during lifespan startup
_app_state: Any = None


def set_app_state(state: Any) -> None:
    """Set the app state reference for job access to HTTP clients.

    Args:
        state: FastAPI app.state object containing HTTP clients.
    """
    global _app_state
    _app_state = state


async def scrape_all_platforms() -> None:
    """Scheduled job to scrape all platforms.

    Creates a ScrapeRun record, executes scraping via orchestrator,
    and updates the record with results or failure status.
    """
    logger.info("Starting scheduled scrape job")

    if _app_state is None:
        logger.error("App state not initialized - cannot run scheduled scrape")
        return

    async with async_session_factory() as db:
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

        try:
            # Create orchestrator with clients from app state
            orchestrator = ScrapingOrchestrator(
                sportybet_client=SportyBetClient(_app_state.sportybet_client),
                betpawa_client=BetPawaClient(_app_state.betpawa_client),
                bet9ja_client=Bet9jaClient(_app_state.bet9ja_client),
            )

            # Execute scrape
            result = await orchestrator.scrape_all(
                scrape_run_id=scrape_run_id,
                db=db,
            )

            # Update ScrapeRun with results
            scrape_run.status = ScrapeStatus(result.status.upper())
            scrape_run.events_scraped = result.total_events
            scrape_run.completed_at = datetime.now(timezone.utc)

            # Count failures from platform results
            failed_count = sum(1 for p in result.platforms if not p.success)
            scrape_run.events_failed = failed_count

            await db.commit()

            logger.info(
                f"Completed ScrapeRun {scrape_run_id}: "
                f"status={result.status}, events={result.total_events}"
            )

        except Exception as e:
            logger.exception(f"ScrapeRun {scrape_run_id} failed: {e}")

            # Update ScrapeRun to FAILED status
            scrape_run.status = ScrapeStatus.FAILED
            scrape_run.completed_at = datetime.now(timezone.utc)
            await db.commit()
