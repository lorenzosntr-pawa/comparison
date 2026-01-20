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


class SchedulerPlatformHealth(BaseModel):
    """Health status for a platform based on scrape history."""

    model_config = ConfigDict(from_attributes=True)

    platform: str
    healthy: bool
    last_success: datetime | None


class RunHistoryEntry(BaseModel):
    """Single scrape run entry for history listing."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: datetime
    completed_at: datetime | None
    events_scraped: int
    events_failed: int
    trigger: str | None
    duration_seconds: float | None


class RunHistoryResponse(BaseModel):
    """Paginated response for scrape run history."""

    model_config = ConfigDict(from_attributes=True)

    runs: list[RunHistoryEntry]
    total: int
