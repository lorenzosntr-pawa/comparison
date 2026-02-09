"""Stale scrape run detection and recovery.

Provides a watchdog job that auto-fails scrape runs stuck in RUNNING status,
and a startup recovery function that cleans up runs left over from a previous
process crash or restart.

Detection Algorithm:
    A run is stale if RUNNING and:
    - Last ScrapePhaseLog.started_at > threshold (default 10 min), OR
    - No phase logs AND ScrapeRun.started_at > threshold

Functions:
    find_stale_runs(): Query for RUNNING runs exceeding threshold
    mark_run_stale(): Update status to FAILED with ScrapeError record
    detect_stale_runs(): Scheduled watchdog job (every 2 minutes)
    recover_stale_runs_on_startup(): Clean up on process restart

Startup Recovery:
    Called BEFORE scheduler starts. Any RUNNING run at startup is stale
    by definition since no orchestrator is active. Marks all as FAILED
    with "process restarted" message.

Error Recording:
    Creates ScrapeError record with error_type="stale" containing:
    - Duration stuck in RUNNING
    - Last known phase and platform
    - Timestamp information

Broadcaster Cleanup:
    When marking a run stale, also closes and removes its ProgressBroadcaster
    to clean up any waiting WebSocket subscribers.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import async_session_factory
from src.db.models.scrape import (
    ScrapeError,
    ScrapePhaseLog,
    ScrapeRun,
    ScrapeStatus,
)
from src.scraping.broadcaster import progress_registry

logger = logging.getLogger(__name__)


async def find_stale_runs(
    db: AsyncSession,
    stale_threshold_minutes: int = 10,
) -> list[tuple[ScrapeRun, datetime | None]]:
    """Find RUNNING scrape runs whose last activity exceeds the threshold.

    Uses MAX(ScrapePhaseLog.started_at) as last activity indicator, falling
    back to ScrapeRun.started_at when no phase logs exist.

    Args:
        db: Async database session.
        stale_threshold_minutes: Minutes of inactivity before a run is stale.

    Returns:
        List of (ScrapeRun, last_activity) tuples for stale runs.
    """
    threshold = datetime.utcnow() - timedelta(minutes=stale_threshold_minutes)

    # Subquery: last activity per run from phase logs
    last_activity_sq = (
        select(
            ScrapePhaseLog.scrape_run_id,
            func.max(ScrapePhaseLog.started_at).label("last_activity"),
        )
        .group_by(ScrapePhaseLog.scrape_run_id)
        .subquery()
    )

    # Main query: RUNNING runs with stale activity
    stmt = (
        select(ScrapeRun, last_activity_sq.c.last_activity)
        .outerjoin(
            last_activity_sq,
            ScrapeRun.id == last_activity_sq.c.scrape_run_id,
        )
        .where(ScrapeRun.status == ScrapeStatus.RUNNING)
        .where(
            # Stale if last phase activity is old, or no phases and run start is old
            (last_activity_sq.c.last_activity < threshold)
            | (
                (last_activity_sq.c.last_activity.is_(None))
                & (ScrapeRun.started_at < threshold)
            )
        )
    )

    result = await db.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]


async def mark_run_stale(
    db: AsyncSession,
    run: ScrapeRun,
    last_activity: datetime | None,
    message: str | None = None,
) -> None:
    """Mark a scrape run as FAILED due to staleness.

    Only updates if the run is still in RUNNING status (optimistic check).

    Args:
        db: Async database session.
        run: The stale ScrapeRun to fail.
        last_activity: Timestamp of last detected activity, or None.
        message: Optional custom error message.
    """
    # Optimistic check: only update if still RUNNING
    if run.status != ScrapeStatus.RUNNING:
        return

    now = datetime.utcnow()

    if last_activity is not None and last_activity.tzinfo is not None:
        last_activity = last_activity.replace(tzinfo=None)

    if message is None:
        if last_activity:
            stale_duration = now - last_activity
            minutes_stale = int(stale_duration.total_seconds() / 60)
            message = (
                f"Run stuck in RUNNING for {minutes_stale}min since last activity. "
                f"Last phase: {run.current_phase or 'unknown'}, "
                f"last platform: {run.current_platform or 'unknown'}"
            )
        else:
            started_at = run.started_at
            if started_at.tzinfo is not None:
                started_at = started_at.replace(tzinfo=None)
            stale_duration = now - started_at
            minutes_stale = int(stale_duration.total_seconds() / 60)
            message = (
                f"Run stuck in RUNNING for {minutes_stale}min with no phase activity. "
                f"Started at: {run.started_at.isoformat()}"
            )

    run.status = ScrapeStatus.FAILED
    run.completed_at = now

    error = ScrapeError(
        scrape_run_id=run.id,
        error_type="stale",
        error_message=message,
    )
    db.add(error)
    await db.flush()


async def detect_stale_runs() -> None:
    """Scheduled watchdog job: detect and fail stale scrape runs.

    Creates its own database session. Finds all RUNNING runs that exceed
    the staleness threshold, marks them as FAILED, cleans up broadcasters,
    and commits once at the end.
    """
    async with async_session_factory() as db:
        stale_runs = await find_stale_runs(db)

        if not stale_runs:
            logger.debug("No stale scrape runs detected")
            return

        for run, last_activity in stale_runs:
            # Re-check status in case orchestrator completed it
            await db.refresh(run)
            if run.status != ScrapeStatus.RUNNING:
                continue

            await mark_run_stale(db, run, last_activity)

            # Clean up broadcaster if exists
            broadcaster = progress_registry.get_broadcaster(run.id)
            if broadcaster:
                await broadcaster.close()
                progress_registry.remove_broadcaster(run.id)

        await db.commit()
        logger.warning(f"Marked {len(stale_runs)} stale scrape run(s) as FAILED")


async def recover_stale_runs_on_startup() -> int:
    """Recover any RUNNING scrape runs left from a previous process.

    At startup, any run still in RUNNING status is stale by definition
    since no orchestrator is active yet. This should be called BEFORE
    the scheduler starts.

    Returns:
        Count of recovered runs.
    """
    async with async_session_factory() as db:
        stmt = select(ScrapeRun).where(ScrapeRun.status == ScrapeStatus.RUNNING)
        result = await db.execute(stmt)
        running_runs = result.scalars().all()

        if not running_runs:
            logger.info("No stale runs to recover on startup")
            return 0

        for run in running_runs:
            await mark_run_stale(
                db,
                run,
                last_activity=None,
                message=(
                    "Run recovered on server startup: process restarted "
                    "while scrape was in progress"
                ),
            )

        await db.commit()
        logger.warning(
            f"Recovered {len(running_runs)} stale scrape run(s) on startup"
        )
        return len(running_runs)
