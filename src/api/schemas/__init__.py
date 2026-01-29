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
    EventMetricsByPlatform,
    EventScrapeMetricsResponse,
    JobStatus,
    PlatformMetric,
    RetryRequest,
    RetryResponse,
    RunHistoryEntry,
    RunHistoryResponse,
    SchedulerPlatformHealth,
    SchedulerStatus,
    ScrapeAnalyticsResponse,
    ScrapePhaseLogResponse,
    ScrapeRunResponse,
    ScrapeStatsResponse,
    SingleEventPlatformResult,
    SingleEventScrapeResponse,
)
from src.api.schemas.settings import (
    SettingsResponse,
    SettingsUpdate,
)
from src.api.schemas.palimpsest import (
    CoverageStats,
    PalimpsestEvent,
    PalimpsestEventsResponse,
    PlatformCoverage,
    TournamentCoverage,
    TournamentGroup,
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
    "EventMetricsByPlatform",
    "EventScrapeMetricsResponse",
    "JobStatus",
    "PlatformMetric",
    "RetryRequest",
    "RetryResponse",
    "RunHistoryEntry",
    "RunHistoryResponse",
    "SchedulerPlatformHealth",
    "SchedulerStatus",
    "ScrapeAnalyticsResponse",
    "ScrapePhaseLogResponse",
    "ScrapeRunResponse",
    "ScrapeStatsResponse",
    "SingleEventPlatformResult",
    "SingleEventScrapeResponse",
    # Settings schemas
    "SettingsResponse",
    "SettingsUpdate",
    # Palimpsest schemas
    "CoverageStats",
    "PalimpsestEvent",
    "PalimpsestEventsResponse",
    "PlatformCoverage",
    "TournamentCoverage",
    "TournamentGroup",
]
