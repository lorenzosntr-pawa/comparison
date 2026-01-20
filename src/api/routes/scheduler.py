"""Scheduler monitoring endpoints for status and run history."""

from apscheduler.triggers.interval import IntervalTrigger
from fastapi import APIRouter

from src.api.schemas.scheduler import JobStatus, SchedulerStatus
from src.scheduling.scheduler import scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status() -> SchedulerStatus:
    """Get current scheduler status and job information.

    Returns:
        SchedulerStatus with running state and list of configured jobs.
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

    return SchedulerStatus(running=scheduler.running, jobs=jobs)
