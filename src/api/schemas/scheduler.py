"""Pydantic schemas for scheduler monitoring endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobStatus(BaseModel):
    """Status information for a scheduled job."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    next_run: datetime | None
    trigger_type: str
    interval_minutes: int | None


class SchedulerStatus(BaseModel):
    """Overall scheduler status with job list."""

    model_config = ConfigDict(from_attributes=True)

    running: bool
    jobs: list[JobStatus]
