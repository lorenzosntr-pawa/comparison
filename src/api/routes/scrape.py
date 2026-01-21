"""Scrape API endpoints for triggering and monitoring scrape operations."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from src.api.schemas import (
    DailyMetric,
    PlatformMetric,
    RetryRequest,
    RetryResponse,
    ScrapeAnalyticsResponse,
    ScrapeErrorResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeRunResponse,
    ScrapeStatsResponse,
    ScrapeStatusResponse,
)
from src.scraping.schemas import Platform
from src.db.engine import get_db
from src.db.models.scrape import ScrapeError, ScrapeRun, ScrapeStatus
from src.scraping.broadcaster import progress_registry
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.orchestrator import ScrapingOrchestrator

router = APIRouter(prefix="/scrape", tags=["scrape"])

# Map orchestrator status strings to ScrapeStatus enum
_STATUS_MAP = {
    "completed": ScrapeStatus.COMPLETED,
    "partial": ScrapeStatus.PARTIAL,
    "failed": ScrapeStatus.FAILED,
}


@router.post("", response_model=ScrapeResponse)
async def trigger_scrape(
    request: Request,
    db: AsyncSession = Depends(get_db),
    body: ScrapeRequest | None = None,
    detail: str = Query(
        default="summary",
        enum=["summary", "full"],
        description="Response detail level",
    ),
    timeout: int = Query(
        default=300,
        ge=5,
        le=600,
        description="Timeout per platform in seconds (default 300s for full scrape)",
    ),
) -> ScrapeResponse:
    """Trigger a scrape operation across selected platforms.

    - **platforms**: Which platforms to scrape (default: all)
    - **detail**: "summary" for counts only, "full" to include all event data
    - **timeout**: Max seconds per platform (default 300, max 600)

    Returns scrape results with status and per-platform breakdown.
    Creates ScrapeRun record to track execution.
    """
    # Create ScrapeRun record at start
    scrape_run = ScrapeRun(
        status=ScrapeStatus.RUNNING,
        trigger="api",
    )
    db.add(scrape_run)
    await db.commit()
    await db.refresh(scrape_run)
    scrape_run_id = scrape_run.id

    # Build scraper clients from app state
    sportybet = SportyBetClient(request.app.state.sportybet_client)
    betpawa = BetPawaClient(request.app.state.betpawa_client)
    bet9ja = Bet9jaClient(request.app.state.bet9ja_client)

    orchestrator = ScrapingOrchestrator(sportybet, betpawa, bet9ja)

    # Execute scrape with DB session for error logging
    include_data = detail == "full"
    result = await orchestrator.scrape_all(
        platforms=body.platforms if body else None,
        sport_id=body.sport_id if body else None,
        competition_id=body.competition_id if body else None,
        include_data=include_data,
        timeout=float(timeout),
        scrape_run_id=scrape_run_id,
        db=db,
    )

    # Update ScrapeRun with results
    scrape_run.status = _STATUS_MAP[result.status]
    scrape_run.completed_at = datetime.utcnow()
    scrape_run.events_scraped = result.total_events
    scrape_run.events_failed = sum(
        1 for p in result.platforms if not p.success
    )

    # Store per-platform timing metrics
    scrape_run.platform_timings = {
        p.platform.value: {
            "duration_ms": p.duration_ms,
            "events_count": p.events_count,
        }
        for p in result.platforms
        if p.success
    }

    await db.commit()

    # Extract events from platform results if detail=full
    events = None
    if include_data:
        events = []
        for platform_result in result.platforms:
            if platform_result.events:
                events.extend(platform_result.events)

    return ScrapeResponse(
        scrape_run_id=scrape_run_id,
        status=result.status,
        started_at=result.started_at,
        completed_at=result.completed_at,
        platforms=result.platforms,
        total_events=result.total_events,
        events=events if include_data else None,
    )


@router.get("/stream")
async def stream_scrape(
    request: Request,
    db: AsyncSession = Depends(get_db),
    timeout: int = Query(
        default=300,
        ge=5,
        le=600,
        description="Timeout per platform in seconds",
    ),
) -> StreamingResponse:
    """Stream scrape progress via Server-Sent Events.

    Connect via EventSource in browser to receive real-time progress updates.
    Each event is a JSON object with platform, phase, counts, and message.

    Returns SSE stream with progress updates for each platform as scraping runs.
    """
    # Create ScrapeRun record
    scrape_run = ScrapeRun(status=ScrapeStatus.RUNNING, trigger="api-stream")
    db.add(scrape_run)
    await db.commit()
    await db.refresh(scrape_run)

    # Build orchestrator
    sportybet = SportyBetClient(request.app.state.sportybet_client)
    betpawa = BetPawaClient(request.app.state.betpawa_client)
    bet9ja = Bet9jaClient(request.app.state.bet9ja_client)
    orchestrator = ScrapingOrchestrator(sportybet, betpawa, bet9ja)

    async def event_generator():
        # Accumulate platform data from progress events
        platform_timings: dict[str, dict] = {}
        total_events = 0
        failed_count = 0
        final_status = ScrapeStatus.COMPLETED

        try:
            async for progress in orchestrator.scrape_with_progress(
                timeout=float(timeout),
                scrape_run_id=scrape_run.id,
                db=db,
            ):
                if await request.is_disconnected():
                    break

                # Accumulate platform timing data from completed events
                if progress.platform and progress.phase == "completed":
                    platform_timings[progress.platform.value] = {
                        "duration_ms": progress.duration_ms or 0,
                        "events_count": progress.events_count or 0,
                    }
                    total_events += progress.events_count or 0
                elif progress.platform and progress.phase == "failed":
                    failed_count += 1

                # Check final status from overall completion event
                if progress.platform is None and progress.phase in ("completed", "failed"):
                    if progress.phase == "failed":
                        final_status = ScrapeStatus.FAILED
                    elif failed_count > 0 and len(platform_timings) > 0:
                        final_status = ScrapeStatus.PARTIAL
                    elif failed_count > 0:
                        final_status = ScrapeStatus.FAILED
                    else:
                        final_status = ScrapeStatus.COMPLETED

                yield f"data: {progress.model_dump_json()}\n\n"
        except Exception as e:
            final_status = ScrapeStatus.FAILED
            yield f"data: {json.dumps({'phase': 'failed', 'message': str(e)})}\n\n"
        finally:
            # Update ScrapeRun with complete data
            scrape_run.status = final_status
            scrape_run.completed_at = datetime.utcnow()
            scrape_run.events_scraped = total_events
            scrape_run.events_failed = failed_count
            scrape_run.platform_timings = platform_timings if platform_timings else None
            await db.commit()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/runs", response_model=list[ScrapeRunResponse])
async def list_scrape_runs(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ScrapeRunResponse]:
    """List scrape runs with pagination.

    Returns most recent runs first, including platform timing breakdown.
    """
    result = await db.execute(
        select(ScrapeRun)
        .order_by(ScrapeRun.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    runs = result.scalars().all()

    return [
        ScrapeRunResponse(
            id=run.id,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            events_scraped=run.events_scraped,
            events_failed=run.events_failed,
            trigger=run.trigger,
            platform_timings=run.platform_timings,
        )
        for run in runs
    ]


@router.get("/stats", response_model=ScrapeStatsResponse)
async def get_scrape_stats(
    db: AsyncSession = Depends(get_db),
) -> ScrapeStatsResponse:
    """Get scrape run statistics."""
    from datetime import timedelta

    from sqlalchemy import func

    # Total runs
    total_result = await db.execute(select(func.count(ScrapeRun.id)))
    total_runs = total_result.scalar() or 0

    # Last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_result = await db.execute(
        select(func.count(ScrapeRun.id)).where(ScrapeRun.started_at > cutoff)
    )
    runs_24h = recent_result.scalar() or 0

    # Average duration (completed runs only)
    avg_result = await db.execute(
        select(
            func.avg(
                func.extract("epoch", ScrapeRun.completed_at - ScrapeRun.started_at)
            )
        ).where(ScrapeRun.completed_at.isnot(None))
    )
    avg_duration_seconds = avg_result.scalar()

    return ScrapeStatsResponse(
        total_runs=total_runs,
        runs_24h=runs_24h,
        avg_duration_seconds=(
            round(avg_duration_seconds, 1) if avg_duration_seconds else None
        ),
    )


@router.get("/analytics", response_model=ScrapeAnalyticsResponse)
async def get_scrape_analytics(
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=14, ge=1, le=30, description="Number of days to analyze"),
) -> ScrapeAnalyticsResponse:
    """Get historical analytics for scrape runs.

    Returns aggregated daily metrics and per-platform statistics
    for the specified time period.
    """
    from collections import defaultdict
    from datetime import timedelta

    from sqlalchemy import case, cast, func, Date

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query daily aggregations
    # Filter to completed, partial, failed runs only (exclude pending/running)
    status_filter = ScrapeRun.status.in_(
        [ScrapeStatus.COMPLETED, ScrapeStatus.PARTIAL, ScrapeStatus.FAILED]
    )
    date_filter = ScrapeRun.started_at >= start_date

    # Daily metrics aggregation
    daily_query = (
        select(
            cast(ScrapeRun.started_at, Date).label("date"),
            func.avg(
                func.extract("epoch", ScrapeRun.completed_at - ScrapeRun.started_at)
            ).label("avg_duration"),
            func.sum(ScrapeRun.events_scraped).label("total_events"),
            func.sum(
                case((ScrapeRun.status == ScrapeStatus.COMPLETED, 1), else_=0)
            ).label("success_count"),
            func.sum(
                case((ScrapeRun.status == ScrapeStatus.FAILED, 1), else_=0)
            ).label("failure_count"),
            func.sum(
                case((ScrapeRun.status == ScrapeStatus.PARTIAL, 1), else_=0)
            ).label("partial_count"),
        )
        .where(status_filter, date_filter, ScrapeRun.completed_at.isnot(None))
        .group_by(cast(ScrapeRun.started_at, Date))
        .order_by(cast(ScrapeRun.started_at, Date))
    )

    daily_result = await db.execute(daily_query)
    daily_rows = daily_result.all()

    daily_metrics = [
        DailyMetric(
            date=row.date.isoformat(),
            avg_duration_seconds=round(row.avg_duration or 0, 1),
            total_events=row.total_events or 0,
            success_count=row.success_count or 0,
            failure_count=row.failure_count or 0,
            partial_count=row.partial_count or 0,
        )
        for row in daily_rows
    ]

    # Platform metrics aggregation from platform_timings JSON
    # Fetch all runs with platform_timings in the date range
    platform_query = (
        select(ScrapeRun.platform_timings, ScrapeRun.status)
        .where(
            status_filter,
            date_filter,
            ScrapeRun.platform_timings.isnot(None),
        )
    )
    platform_result = await db.execute(platform_query)
    platform_rows = platform_result.all()

    # Aggregate platform data
    platform_stats: dict[str, dict] = defaultdict(
        lambda: {
            "total_duration_ms": 0,
            "total_events": 0,
            "run_count": 0,
            "success_count": 0,
        }
    )

    for row in platform_rows:
        timings = row.platform_timings
        if not timings:
            continue
        for platform, data in timings.items():
            stats = platform_stats[platform]
            stats["total_duration_ms"] += data.get("duration_ms", 0)
            stats["total_events"] += data.get("events_count", 0)
            stats["run_count"] += 1
            # If platform appears in timings, it succeeded for this run
            stats["success_count"] += 1

    platform_metrics = [
        PlatformMetric(
            platform=platform,
            success_rate=(
                round((stats["success_count"] / stats["run_count"]) * 100, 1)
                if stats["run_count"] > 0
                else 0
            ),
            avg_duration_seconds=(
                round((stats["total_duration_ms"] / stats["run_count"]) / 1000, 1)
                if stats["run_count"] > 0
                else 0
            ),
            total_events=stats["total_events"],
        )
        for platform, stats in sorted(platform_stats.items())
    ]

    return ScrapeAnalyticsResponse(
        daily_metrics=daily_metrics,
        platform_metrics=platform_metrics,
        period_start=start_date.date().isoformat(),
        period_end=end_date.date().isoformat(),
    )


@router.post("/{run_id}/retry", response_model=RetryResponse)
async def retry_scrape_run(
    run_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    body: RetryRequest | None = None,
    timeout: int = Query(
        default=300,
        ge=5,
        le=600,
        description="Timeout per platform in seconds",
    ),
) -> RetryResponse:
    """Retry failed platforms from a previous scrape run.

    Creates a new scrape run targeting only the specified platforms
    (or all failed platforms if none specified). The original run
    is preserved for audit trail.

    - **run_id**: ID of the scrape run to retry
    - **platforms**: List of platform names to retry (empty = all failed)
    - **timeout**: Max seconds per platform

    Returns 400 if run is still running, or if no platforms need retry.
    """
    # Fetch the original run with errors
    result = await db.execute(
        select(ScrapeRun)
        .options(selectinload(ScrapeRun.errors).selectinload(ScrapeError.bookmaker))
        .where(ScrapeRun.id == run_id)
    )
    original_run = result.scalar_one_or_none()

    if not original_run:
        raise HTTPException(status_code=404, detail="Scrape run not found")

    # Can't retry a running scrape
    if original_run.status == ScrapeStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot retry a running scrape. Wait for it to complete.",
        )

    # Determine which platforms to retry
    requested_platforms = body.platforms if body and body.platforms else []

    # Get platforms that failed (from errors or missing from timings)
    failed_platforms: set[str] = set()

    # Add platforms from errors
    if original_run.errors:
        for error in original_run.errors:
            if error.bookmaker and error.bookmaker.slug:
                failed_platforms.add(error.bookmaker.slug)

    # Add platforms missing from successful timings (for partial failures)
    all_platform_slugs = {p.value for p in Platform}
    if original_run.platform_timings:
        successful_platforms = set(original_run.platform_timings.keys())
        failed_platforms.update(all_platform_slugs - successful_platforms)
    elif original_run.status in (ScrapeStatus.PARTIAL, ScrapeStatus.FAILED):
        # No timings but partial/failed = all platforms failed
        failed_platforms = all_platform_slugs

    # If specific platforms requested, validate them
    if requested_platforms:
        # Validate all requested platforms are valid Platform enum values
        invalid_platforms = [
            p for p in requested_platforms if p not in all_platform_slugs
        ]
        if invalid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platform names: {invalid_platforms}. Valid: {sorted(all_platform_slugs)}",
            )

        # Use requested platforms (user might want to retry even if it succeeded before)
        platforms_to_retry = requested_platforms
    else:
        # Retry all failed platforms
        platforms_to_retry = list(failed_platforms)

    if not platforms_to_retry:
        raise HTTPException(
            status_code=400,
            detail="No platforms to retry. All platforms succeeded in the original run.",
        )

    # Convert platform strings to Platform enum
    platform_enums = [Platform(p) for p in platforms_to_retry]

    # Create new ScrapeRun for the retry
    retry_run = ScrapeRun(
        status=ScrapeStatus.RUNNING,
        trigger=f"retry:{run_id}",
    )
    db.add(retry_run)
    await db.commit()
    await db.refresh(retry_run)

    # Build orchestrator and execute scrape
    sportybet = SportyBetClient(request.app.state.sportybet_client)
    betpawa = BetPawaClient(request.app.state.betpawa_client)
    bet9ja = Bet9jaClient(request.app.state.bet9ja_client)
    orchestrator = ScrapingOrchestrator(sportybet, betpawa, bet9ja)

    result = await orchestrator.scrape_all(
        platforms=platform_enums,
        include_data=False,
        timeout=float(timeout),
        scrape_run_id=retry_run.id,
        db=db,
    )

    # Update retry run with results
    retry_run.status = _STATUS_MAP[result.status]
    retry_run.completed_at = datetime.utcnow()
    retry_run.events_scraped = result.total_events
    retry_run.events_failed = sum(1 for p in result.platforms if not p.success)
    retry_run.platform_timings = {
        p.platform.value: {
            "duration_ms": p.duration_ms,
            "events_count": p.events_count,
        }
        for p in result.platforms
        if p.success
    }

    await db.commit()

    return RetryResponse(
        new_run_id=retry_run.id,
        platforms_retried=platforms_to_retry,
        message=f"Retry {result.status}: {len(platforms_to_retry)} platform(s) retried",
    )


@router.get("/{scrape_run_id}", response_model=ScrapeStatusResponse)
async def get_scrape_status(
    scrape_run_id: int,
    db: AsyncSession = Depends(get_db),
) -> ScrapeStatusResponse:
    """Get status of a scrape run by ID.

    Returns current status, counts, timing information, and any errors.
    """
    result = await db.execute(
        select(ScrapeRun)
        .options(selectinload(ScrapeRun.errors).selectinload(ScrapeError.bookmaker))
        .where(ScrapeRun.id == scrape_run_id)
    )
    scrape_run = result.scalar_one_or_none()

    if not scrape_run:
        raise HTTPException(status_code=404, detail="Scrape run not found")

    # Build error responses with platform name from bookmaker
    errors = None
    if scrape_run.errors:
        errors = [
            ScrapeErrorResponse(
                id=err.id,
                error_type=err.error_type,
                error_message=err.error_message,
                occurred_at=err.occurred_at,
                platform=err.bookmaker.name if err.bookmaker else None,
            )
            for err in scrape_run.errors
        ]

    return ScrapeStatusResponse(
        scrape_run_id=scrape_run.id,
        status=scrape_run.status,
        started_at=scrape_run.started_at,
        completed_at=scrape_run.completed_at,
        events_scraped=scrape_run.events_scraped,
        events_failed=scrape_run.events_failed,
        trigger=scrape_run.trigger,
        platform_timings=scrape_run.platform_timings,
        errors=errors,
    )


@router.get("/runs/{scrape_run_id}/progress")
async def observe_scrape_progress(
    scrape_run_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Observe progress of an existing scrape run via SSE.

    Connect via EventSource in browser to receive real-time progress updates
    for a specific scrape run (including scheduled scrapes).

    Unlike /stream which starts a new scrape, this endpoint observes an
    existing running scrape.

    Returns 404 if scrape run not found.
    Returns 410 (Gone) if scrape already completed.
    """
    # Verify scrape run exists
    result = await db.execute(
        select(ScrapeRun).where(ScrapeRun.id == scrape_run_id)
    )
    scrape_run = result.scalar_one_or_none()

    if not scrape_run:
        raise HTTPException(status_code=404, detail="Scrape run not found")

    # Check if already completed
    if scrape_run.status != ScrapeStatus.RUNNING:
        raise HTTPException(
            status_code=410,
            detail=f"Scrape run already {scrape_run.status.value}",
        )

    # Get broadcaster for this scrape
    broadcaster = progress_registry.get_broadcaster(scrape_run_id)

    if not broadcaster:
        # No broadcaster means scrape is running but not using progress streaming
        # This can happen for older API-triggered scrapes or if scheduler
        # hasn't been updated. Return empty stream that closes immediately.
        async def empty_generator():
            yield f"data: {json.dumps({'phase': 'unknown', 'message': 'No progress streaming available for this scrape run'})}\n\n"

        return StreamingResponse(
            empty_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def event_generator():
        try:
            async for progress in broadcaster.subscribe():
                if await request.is_disconnected():
                    break
                yield f"data: {progress.model_dump_json()}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'phase': 'failed', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/runs/active")
async def get_active_scrapes() -> list[int]:
    """Get IDs of currently running scrapes with progress streaming.

    Returns list of scrape run IDs that have active progress broadcasters.
    Useful for frontend to discover running scrapes to observe.
    """
    return progress_registry.get_active_scrape_ids()
