"""API schemas for request/response models."""

from src.api.schemas.api import (
    HealthResponse,
    PlatformHealth,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeStatusResponse,
)
from src.api.schemas.scheduler import (
    JobStatus,
    RunHistoryEntry,
    RunHistoryResponse,
    SchedulerPlatformHealth,
    SchedulerStatus,
)

__all__ = [
    # API schemas
    "HealthResponse",
    "PlatformHealth",
    "ScrapeRequest",
    "ScrapeResponse",
    "ScrapeStatusResponse",
    # Scheduler schemas
    "JobStatus",
    "RunHistoryEntry",
    "RunHistoryResponse",
    "SchedulerPlatformHealth",
    "SchedulerStatus",
]
