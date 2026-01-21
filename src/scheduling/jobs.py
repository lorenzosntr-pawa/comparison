"""Scheduled job functions for periodic scraping."""

import logging
from datetime import datetime
from typing import Any

from src.db.engine import async_session_factory
from src.db.models.scrape import ScrapeRun, ScrapeStatus
from src.scraping.broadcaster import progress_registry
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

    Creates a ScrapeRun record, executes scraping via orchestrator with
    progress streaming, and updates the record with results or failure status.

    Progress is published to a broadcaster so UI can observe via SSE.
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

        # Create broadcaster for this scrape run
        broadcaster = progress_registry.create_broadcaster(scrape_run_id)

        try:
            # Create orchestrator with clients from app state
            orchestrator = ScrapingOrchestrator(
                sportybet_client=SportyBetClient(_app_state.sportybet_client),
                betpawa_client=BetPawaClient(_app_state.betpawa_client),
                bet9ja_client=Bet9jaClient(_app_state.bet9ja_client),
            )

            # Execute scrape with progress streaming
            # scrape_with_progress yields progress updates sequentially
            total_events = 0
            final_status = "failed"

            async for progress in orchestrator.scrape_with_progress(
                timeout=300.0,
                scrape_run_id=scrape_run_id,
                db=db,
            ):
                # Publish progress to broadcaster for SSE observers
                await broadcaster.publish(progress)

                # Track final state
                if progress.phase == "completed" and progress.platform is None:
                    # Final completion update
                    total_events = progress.events_count or 0
                    final_status = "completed"
                elif progress.phase == "completed" and progress.platform:
                    # Platform completed
                    total_events += progress.events_count or 0
                elif progress.phase == "failed" and progress.platform is None:
                    # Overall failure
                    final_status = "failed"

            # Determine status based on progress history
            # If we got here, scrape completed (possibly with partial success)
            if final_status == "completed" and total_events > 0:
                scrape_run.status = ScrapeStatus.COMPLETED
            elif total_events > 0:
                scrape_run.status = ScrapeStatus.PARTIAL
            else:
                scrape_run.status = ScrapeStatus.FAILED

            scrape_run.events_scraped = total_events
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
            # Close broadcaster and remove from registry
            await broadcaster.close()
            progress_registry.remove_broadcaster(scrape_run_id)
