"""Scheduler monitoring endpoints for status and run history."""

from apscheduler.schedulers.base import STATE_PAUSED
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.scheduler import (
    JobStatus,
    RunHistoryEntry,
    RunHistoryResponse,
    SchedulerPlatformHealth,
    SchedulerStatus,
)
from src.db.engine import get_db
from src.db.models.scrape import ScrapeRun, ScrapeStatus
from src.scheduling.scheduler import scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class PauseResumeResponse(BaseModel):
    """Response for pause/resume operations."""

    success: bool
    paused: bool
    message: str


@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status() -> SchedulerStatus:
    """Get current scheduler status and job information.

    Returns:
        SchedulerStatus with running state, paused state, and list of configured jobs.
    """
    jobs = []
    for job in scheduler.get_jobs():
        interval_minutes = None
        if isinstance(job.trigger, IntervalTrigger):
            interval_minutes = int(job.trigger.interval.total_seconds() / 60)
        jobs.append(
            JobStatus(
                id=job.id,
                next_run=job.next_run_time,
                trigger_type=type(job.trigger).__name__,
                interval_minutes=interval_minutes,
            )
        )

    # Check if scheduler is paused using APScheduler's state property
    # STATE_PAUSED indicates scheduler.pause() was called
    paused = scheduler.state == STATE_PAUSED

    return SchedulerStatus(running=scheduler.running, paused=paused, jobs=jobs)


@router.post("/pause", response_model=PauseResumeResponse)
async def pause_scheduler() -> PauseResumeResponse:
    """Pause the scheduler (stops job execution without stopping scheduler).

    Returns:
        PauseResumeResponse indicating success and current paused state.
    """
    if not scheduler.running:
        return PauseResumeResponse(
            success=False,
            paused=False,
            message="Scheduler is not running",
        )

    scheduler.pause()
    return PauseResumeResponse(
        success=True,
        paused=True,
        message="Scheduler paused successfully",
    )


@router.post("/resume", response_model=PauseResumeResponse)
async def resume_scheduler() -> PauseResumeResponse:
    """Resume the scheduler (restarts job execution).

    Returns:
        PauseResumeResponse indicating success and current paused state.
    """
    if not scheduler.running:
        return PauseResumeResponse(
            success=False,
            paused=False,
            message="Scheduler is not running",
        )

    scheduler.resume()
    return PauseResumeResponse(
        success=True,
        paused=False,
        message="Scheduler resumed successfully",
    )


@router.get("/history", response_model=RunHistoryResponse)
async def get_run_history(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
) -> RunHistoryResponse:
    """Get paginated scrape run history.

    Args:
        db: Database session.
        limit: Maximum number of runs to return (1-100, default 20).
        offset: Number of runs to skip (default 0).
        status: Optional filter by status (pending, running, completed, partial, failed).

    Returns:
        RunHistoryResponse with paginated list of scrape runs and total count.
    """
    # Build base query
    query = select(ScrapeRun).order_by(ScrapeRun.started_at.desc())
    count_query = select(func.count(ScrapeRun.id))

    # Apply status filter if provided
    if status:
        query = query.where(ScrapeRun.status == status)
        count_query = count_query.where(ScrapeRun.status == status)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    runs = result.scalars().all()

    # Convert to response models
    entries = []
    for run in runs:
        duration_seconds = None
        if run.completed_at and run.started_at:
            duration_seconds = (run.completed_at - run.started_at).total_seconds()

        entries.append(
            RunHistoryEntry(
                id=run.id,
                status=run.status,
                started_at=run.started_at,
                completed_at=run.completed_at,
                events_scraped=run.events_scraped,
                events_failed=run.events_failed,
                trigger=run.trigger,
                duration_seconds=duration_seconds,
                platform_timings=run.platform_timings,
            )
        )

    return RunHistoryResponse(runs=entries, total=total)


@router.get("/health", response_model=list[SchedulerPlatformHealth])
async def get_platform_health(
    db: AsyncSession = Depends(get_db),
) -> list[SchedulerPlatformHealth]:
    """Get platform health status based on recent scrape runs.

    Returns health status for each platform based on the most recent
    successful scrape timestamp.

    Returns:
        List of SchedulerPlatformHealth entries for each platform.
    """
    # Get the most recent completed scrape run
    query = (
        select(ScrapeRun)
        .where(ScrapeRun.status.in_([ScrapeStatus.COMPLETED, ScrapeStatus.PARTIAL]))
        .order_by(ScrapeRun.started_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    last_run = result.scalar_one_or_none()

    # Define platforms to check
    platforms = ["sportybet", "betpawa", "bet9ja"]

    # For now, platform health is based on whether there's been a recent successful scrape
    # In the future, this could be enhanced to check per-platform errors
    health_entries = []
    for platform in platforms:
        health_entries.append(
            SchedulerPlatformHealth(
                platform=platform,
                healthy=last_run is not None,
                last_success=last_run.completed_at if last_run else None,
            )
        )

    return health_entries
