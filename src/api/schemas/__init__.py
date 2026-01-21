"""API schemas for request/response models."""

from src.api.schemas.api import (
    HealthResponse,
    PlatformHealth,
    ScrapeErrorResponse,
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
    ScrapeRunResponse,
    ScrapeStatsResponse,
)

__all__ = [
    # API schemas
    "HealthResponse",
    "PlatformHealth",
    "ScrapeErrorResponse",
    "ScrapeRequest",
    "ScrapeResponse",
    "ScrapeStatusResponse",
    # Scheduler schemas
    "JobStatus",
    "RunHistoryEntry",
    "RunHistoryResponse",
    "SchedulerPlatformHealth",
    "SchedulerStatus",
    "ScrapeRunResponse",
    "ScrapeStatsResponse",
]
