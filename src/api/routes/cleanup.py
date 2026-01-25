"""Cleanup API endpoints for data retention management."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.cleanup import (
    CleanupExecuteRequest,
    CleanupHistoryResponse,
    CleanupPreview,
    CleanupResult,
    CleanupRunResponse,
    CleanupStatusResponse,
    DataStats,
)
from src.db.engine import get_db
from src.db.models.cleanup_run import CleanupRun
from src.db.models.settings import Settings
from src.scheduling.jobs import is_scraping_active
from src.services.cleanup import (
    execute_cleanup_with_tracking,
    get_data_stats,
    preview_cleanup,
)

router = APIRouter(prefix="/cleanup", tags=["cleanup"])

# Track if cleanup is currently running
_cleanup_running = False


async def get_settings_values(db: AsyncSession) -> tuple[int, int]:
    """Get current retention settings values.

    Returns:
        Tuple of (odds_retention_days, match_retention_days).
    """
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings = result.scalar_one_or_none()

    if settings is None:
        return 30, 30  # Default values

    return settings.odds_retention_days, settings.match_retention_days


@router.get("/stats", response_model=DataStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> DataStats:
    """Get comprehensive data statistics for all tables.

    Returns counts, date ranges, and platform breakdowns.
    """
    return await get_data_stats(db)


@router.get("/preview", response_model=CleanupPreview)
async def get_preview(
    odds_days: int | None = Query(None, ge=1, le=365, description="Days for odds retention"),
    match_days: int | None = Query(None, ge=1, le=365, description="Days for match retention"),
    db: AsyncSession = Depends(get_db),
) -> CleanupPreview:
    """Preview what would be deleted by cleanup.

    If days parameters are not provided, uses current settings values.
    """
    default_odds, default_match = await get_settings_values(db)

    return await preview_cleanup(
        session=db,
        odds_days=odds_days or default_odds,
        match_days=match_days or default_match,
    )


@router.post("/execute", response_model=CleanupResult)
async def execute(
    request: CleanupExecuteRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> CleanupResult:
    """Execute cleanup of old data.

    Records as 'manual' trigger in cleanup_runs table.
    If retention days not provided, uses current settings values.
    """
    global _cleanup_running

    if _cleanup_running:
        raise Exception("Cleanup is already running")

    _cleanup_running = True

    try:
        default_odds, default_match = await get_settings_values(db)

        odds_days = default_odds
        match_days = default_match

        if request:
            if request.odds_retention_days is not None:
                odds_days = request.odds_retention_days
            if request.match_retention_days is not None:
                match_days = request.match_retention_days

        _, result = await execute_cleanup_with_tracking(
            session=db,
            odds_days=odds_days,
            match_days=match_days,
            trigger="manual",
        )

        return result
    finally:
        _cleanup_running = False


@router.get("/history", response_model=CleanupHistoryResponse)
async def get_history(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of runs to return"),
    db: AsyncSession = Depends(get_db),
) -> CleanupHistoryResponse:
    """Get list of recent cleanup runs.

    Returns cleanup run history ordered by most recent first.
    """
    # Get total count
    count_result = await db.execute(select(func.count(CleanupRun.id)))
    total = count_result.scalar_one()

    # Get recent runs
    result = await db.execute(
        select(CleanupRun)
        .order_by(desc(CleanupRun.started_at))
        .limit(limit)
    )
    runs = result.scalars().all()

    return CleanupHistoryResponse(
        runs=[CleanupRunResponse.model_validate(run) for run in runs],
        total=total,
    )


@router.get("/status", response_model=CleanupStatusResponse)
async def get_status() -> CleanupStatusResponse:
    """Get current cleanup and scraping activity status.

    Used by frontend for status indicators.
    """
    return CleanupStatusResponse(
        is_cleanup_running=_cleanup_running,
        is_scraping_active=is_scraping_active(),
    )
