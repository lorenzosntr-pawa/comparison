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
    DailyMetric,
    JobStatus,
    PlatformMetric,
    RetryRequest,
    RetryResponse,
    RunHistoryEntry,
    RunHistoryResponse,
    SchedulerPlatformHealth,
    SchedulerStatus,
    ScrapeAnalyticsResponse,
    ScrapeRunResponse,
    ScrapeStatsResponse,
)
from src.api.schemas.settings import (
    SettingsResponse,
    SettingsUpdate,
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
    "DailyMetric",
    "JobStatus",
    "PlatformMetric",
    "RetryRequest",
    "RetryResponse",
    "RunHistoryEntry",
    "RunHistoryResponse",
    "SchedulerPlatformHealth",
    "SchedulerStatus",
    "ScrapeAnalyticsResponse",
    "ScrapeRunResponse",
    "ScrapeStatsResponse",
    # Settings schemas
    "SettingsResponse",
    "SettingsUpdate",
]
