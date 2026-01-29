"""Scrape API endpoints for triggering and monitoring scrape operations."""

import asyncio
import json
import time
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from src.api.schemas import (
    DailyMetric,
    EventMetricsByPlatform,
    EventScrapeMetricsResponse,
    PlatformMetric,
    RetryRequest,
    RetryResponse,
    ScrapeAnalyticsResponse,
    ScrapeErrorResponse,
    ScrapePhaseLogResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeRunResponse,
    ScrapeStatsResponse,
    ScrapeStatusResponse,
    SingleEventPlatformResult,
    SingleEventScrapeResponse,
)
from src.scraping.schemas import Platform, ScrapeProgress
from src.db.engine import async_session_factory, get_db
from src.db.models.competitor import CompetitorEvent
from src.db.models.event import Event, EventBookmaker
from src.db.models.event_scrape_status import EventScrapeStatus
from src.db.models.scrape import ScrapeError, ScrapePhaseLog, ScrapeRun, ScrapeStatus
from src.db.models.settings import Settings
from src.scraping.broadcaster import progress_registry
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.event_coordinator import EventCoordinator

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

    # Get settings for EventCoordinator tuning
    settings_result = await db.execute(select(Settings).where(Settings.id == 1))
    settings = settings_result.scalar_one_or_none()

    # Create coordinator
    coordinator = EventCoordinator.from_settings(
        betpawa_client=betpawa,
        sportybet_client=sportybet,
        bet9ja_client=bet9ja,
        settings=settings,
    )

    # Run cycle and collect results
    total_events = 0
    failed_count = 0
    final_status = "completed"

    async for progress in coordinator.run_full_cycle(db=db, scrape_run_id=scrape_run_id):
        if progress.get("event_type") == "CYCLE_COMPLETE":
            total_events = progress.get("events_scraped", 0)
            failed_count = progress.get("events_failed", 0)
            if failed_count > 0 and total_events > 0:
                final_status = "partial"
            elif total_events == 0:
                final_status = "failed"

    # Update ScrapeRun with results
    scrape_run.status = _STATUS_MAP[final_status]
    scrape_run.completed_at = datetime.utcnow()
    scrape_run.events_scraped = total_events
    scrape_run.events_failed = failed_count
    scrape_run.platform_timings = None  # EventCoordinator doesn't track platform-level timings

    await db.commit()

    return ScrapeResponse(
        scrape_run_id=scrape_run_id,
        status=final_status,
        started_at=scrape_run.started_at,
        completed_at=scrape_run.completed_at,
        platforms=[],  # EventCoordinator doesn't return platform-level results
        total_events=total_events,
        events=None,  # EventCoordinator doesn't support include_data
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

    The scrape runs as a background task that continues even if the SSE client
    disconnects. SSE is purely for observation, not execution control.

    Returns SSE stream with progress updates for each platform as scraping runs.
    """
    # Create ScrapeRun record
    scrape_run = ScrapeRun(status=ScrapeStatus.RUNNING, trigger="api-stream")
    db.add(scrape_run)
    await db.commit()
    await db.refresh(scrape_run)
    scrape_run_id = scrape_run.id

    # Create broadcaster for this scrape run before spawning background task
    broadcaster = progress_registry.create_broadcaster(scrape_run_id)

    # Capture app state references for background task (avoids request.app access)
    sportybet_http = request.app.state.sportybet_client
    betpawa_http = request.app.state.betpawa_client
    bet9ja_http = request.app.state.bet9ja_client

    async def run_scrape_background():
        """Background task that runs independent of SSE connection.

        Uses its own DB session to avoid CancelledError when client disconnects.
        Broadcasts progress via progress_registry for SSE subscribers.
        """
        # Track metrics for final update
        total_events = 0
        failed_count = 0
        final_status = ScrapeStatus.COMPLETED

        async with async_session_factory() as bg_db:
            # Build clients with captured HTTP clients
            sportybet = SportyBetClient(sportybet_http)
            betpawa = BetPawaClient(betpawa_http)
            bet9ja = Bet9jaClient(bet9ja_http)

            # Get settings for EventCoordinator tuning
            settings_result = await bg_db.execute(select(Settings).where(Settings.id == 1))
            settings = settings_result.scalar_one_or_none()

            # Create EventCoordinator from settings
            coordinator = EventCoordinator.from_settings(
                betpawa_client=betpawa,
                sportybet_client=sportybet,
                bet9ja_client=bet9ja,
                settings=settings,
            )

            try:
                async for progress_event in coordinator.run_full_cycle(
                    db=bg_db,
                    scrape_run_id=scrape_run_id,
                ):
                    # Convert dict events to ScrapeProgress for broadcaster compatibility
                    event_type = progress_event.get("event_type", "")

                    if event_type == "CYCLE_START":
                        await broadcaster.publish(ScrapeProgress(
                            platform=None,
                            phase="starting",
                            current=0,
                            total=3,
                            message="Starting event-centric scrape cycle",
                        ))
                    elif event_type == "DISCOVERY_COMPLETE":
                        total = progress_event.get("total_events", 0)
                        await broadcaster.publish(ScrapeProgress(
                            platform=None,
                            phase="discovery",
                            current=1,
                            total=3,
                            message=f"Discovered {total} events across all platforms",
                            events_count=total,
                        ))

                        # Disconnect detection after discovery
                        if broadcaster.subscriber_count == 0:
                            log = structlog.get_logger()
                            log.warning(
                                "SSE connection lost during manual scrape",
                                scrape_run_id=scrape_run_id,
                                phase="discovery",
                            )
                            final_status = ScrapeStatus.CONNECTION_FAILED
                            break

                    elif event_type == "BATCH_COMPLETE":
                        processed = progress_event.get("events_stored", 0)
                        await broadcaster.publish(ScrapeProgress(
                            platform=None,
                            phase="scraping",
                            current=2,
                            total=3,
                            message=f"Processed batch: {processed} events stored",
                            events_count=processed,
                        ))
                    elif event_type == "CYCLE_COMPLETE":
                        total_events = progress_event.get("events_scraped", 0)
                        failed_count = progress_event.get("events_failed", 0)
                        total_ms = progress_event.get("total_timing_ms", 0)

                        await broadcaster.publish(ScrapeProgress(
                            platform=None,
                            phase="completed",
                            current=3,
                            total=3,
                            message=f"Completed: {total_events} events scraped ({total_ms}ms)",
                            events_count=total_events,
                            duration_ms=total_ms,
                        ))

                        # Determine final status
                        if failed_count > 0 and total_events > 0:
                            final_status = ScrapeStatus.PARTIAL
                        elif total_events == 0:
                            final_status = ScrapeStatus.FAILED

            except Exception as e:
                final_status = ScrapeStatus.FAILED
                await broadcaster.publish(ScrapeProgress(
                    phase="failed", current=0, total=0, message=str(e)
                ))
            finally:
                # Update ScrapeRun with results (using background DB session)
                scrape_run_obj = await bg_db.get(ScrapeRun, scrape_run_id)
                if scrape_run_obj:
                    scrape_run_obj.status = final_status
                    scrape_run_obj.completed_at = datetime.utcnow()
                    scrape_run_obj.events_scraped = total_events
                    scrape_run_obj.events_failed = failed_count
                    scrape_run_obj.platform_timings = None
                    await bg_db.commit()

                # Signal completion and clean up
                await broadcaster.close()
                progress_registry.remove_broadcaster(scrape_run_id)

    # Start background task (fire-and-forget, survives SSE disconnect)
    asyncio.create_task(run_scrape_background())

    # Small delay to ensure broadcaster is registered and ready
    await asyncio.sleep(0.05)

    async def event_generator():
        """SSE stream that subscribes to progress updates."""
        try:
            async for progress in broadcaster.subscribe():
                if await request.is_disconnected():
                    break
                yield f"data: {progress.model_dump_json()}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'phase': 'error', 'message': str(e)})}\n\n"

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

    # Build EventCoordinator and execute scrape
    sportybet = SportyBetClient(request.app.state.sportybet_client)
    betpawa = BetPawaClient(request.app.state.betpawa_client)
    bet9ja = Bet9jaClient(request.app.state.bet9ja_client)

    # Get settings for EventCoordinator tuning
    settings_result = await db.execute(select(Settings).where(Settings.id == 1))
    settings = settings_result.scalar_one_or_none()

    coordinator = EventCoordinator.from_settings(
        betpawa_client=betpawa,
        sportybet_client=sportybet,
        bet9ja_client=bet9ja,
        settings=settings,
    )

    # Run full cycle (event-centric covers all platforms)
    total_events = 0
    failed_count = 0
    final_status = "completed"

    async for progress in coordinator.run_full_cycle(db=db, scrape_run_id=retry_run.id):
        if progress.get("event_type") == "CYCLE_COMPLETE":
            total_events = progress.get("events_scraped", 0)
            failed_count = progress.get("events_failed", 0)
            if failed_count > 0 and total_events > 0:
                final_status = "partial"
            elif total_events == 0:
                final_status = "failed"

    # Update retry run with results
    retry_run.status = _STATUS_MAP[final_status]
    retry_run.completed_at = datetime.utcnow()
    retry_run.events_scraped = total_events
    retry_run.events_failed = failed_count
    retry_run.platform_timings = None

    await db.commit()

    return RetryResponse(
        new_run_id=retry_run.id,
        platforms_retried=platforms_to_retry,
        message=f"Retry {final_status}: {len(platforms_to_retry)} platform(s) retried",
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
    if scrape_run.status != ScrapeStatus.RUNNING.value:
        raise HTTPException(
            status_code=410,
            detail=f"Scrape run already {scrape_run.status}",
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


@router.get("/runs/{run_id}/phases", response_model=list[ScrapePhaseLogResponse])
async def get_phase_history(
    run_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ScrapePhaseLogResponse]:
    """Get phase transition history for a scrape run.

    Returns ordered list of phase log entries for timeline visualization.
    Each entry shows phase start/end times, platform, message, and error details.
    """
    # Verify scrape run exists
    run_result = await db.execute(select(ScrapeRun).where(ScrapeRun.id == run_id))
    scrape_run = run_result.scalar_one_or_none()
    if not scrape_run:
        raise HTTPException(status_code=404, detail="Scrape run not found")

    # Get phase logs ordered by start time
    result = await db.execute(
        select(ScrapePhaseLog)
        .where(ScrapePhaseLog.scrape_run_id == run_id)
        .order_by(ScrapePhaseLog.started_at.asc())
    )
    phase_logs = result.scalars().all()

    return [
        ScrapePhaseLogResponse(
            id=log.id,
            platform=log.platform,
            phase=log.phase,
            started_at=log.started_at,
            ended_at=log.ended_at,
            events_processed=log.events_processed,
            message=log.message,
        )
        for log in phase_logs
    ]


@router.get("/event-metrics", response_model=EventScrapeMetricsResponse)
async def get_event_scrape_metrics(
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze"),
) -> EventScrapeMetricsResponse:
    """Get per-event scrape metrics from the new EventCoordinator flow.

    Aggregates data from EventScrapeStatus records to provide insights on
    per-event success rates and per-platform performance.

    Returns metrics broken down by platform showing:
    - Total events requested per platform
    - Total events successfully scraped
    - Total events that failed
    - Success rate percentage
    - Average timing in ms
    """
    from collections import defaultdict
    from datetime import timedelta

    from sqlalchemy import func

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query all EventScrapeStatus records in date range
    result = await db.execute(
        select(EventScrapeStatus).where(
            EventScrapeStatus.created_at >= start_date
        )
    )
    records = result.scalars().all()

    # Aggregate metrics
    total_events = len(records)
    events_fully_scraped = 0
    events_partially_scraped = 0
    events_failed = 0

    # Per-platform aggregation
    platform_stats: dict[str, dict] = defaultdict(
        lambda: {
            "requested": 0,
            "scraped": 0,
            "failed": 0,
            "total_timing_ms": 0,
            "timing_count": 0,
        }
    )

    for record in records:
        # Count event outcomes
        if not record.platforms_scraped:
            events_failed += 1
        elif len(record.platforms_scraped) == len(record.platforms_requested):
            events_fully_scraped += 1
        else:
            events_partially_scraped += 1

        # Per-platform stats
        for platform in record.platforms_requested:
            platform_stats[platform]["requested"] += 1

        for platform in record.platforms_scraped:
            platform_stats[platform]["scraped"] += 1
            platform_stats[platform]["total_timing_ms"] += record.timing_ms
            platform_stats[platform]["timing_count"] += 1

        for platform in record.platforms_failed:
            platform_stats[platform]["failed"] += 1

    # Build platform metrics response
    platform_metrics = []
    for platform in sorted(platform_stats.keys()):
        stats = platform_stats[platform]
        success_rate = (
            round((stats["scraped"] / stats["requested"]) * 100, 1)
            if stats["requested"] > 0
            else 0.0
        )
        avg_timing_ms = (
            round(stats["total_timing_ms"] / stats["timing_count"], 1)
            if stats["timing_count"] > 0
            else 0.0
        )
        platform_metrics.append(
            EventMetricsByPlatform(
                platform=platform,
                total_requested=stats["requested"],
                total_scraped=stats["scraped"],
                total_failed=stats["failed"],
                success_rate=success_rate,
                avg_timing_ms=avg_timing_ms,
            )
        )

    return EventScrapeMetricsResponse(
        period_start=start_date.date().isoformat(),
        period_end=end_date.date().isoformat(),
        total_events=total_events,
        events_fully_scraped=events_fully_scraped,
        events_partially_scraped=events_partially_scraped,
        events_failed=events_failed,
        platform_metrics=platform_metrics,
    )


@router.post("/event/{sr_id}", response_model=SingleEventScrapeResponse)
async def scrape_single_event(
    sr_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SingleEventScrapeResponse:
    """Scrape a single event across all available bookmakers.

    Enables manual refresh of a specific event's odds without running a full scrape cycle.
    Useful for traders monitoring specific matches or refreshing stale data.

    - **sr_id**: SportRadar ID of the event (e.g., "12345678")

    Returns per-platform success/failure details and timing information.
    Returns 404 if event not found in any platform database.
    """
    log = structlog.get_logger()
    start_time = time.perf_counter()

    # Build platform_ids dict by looking up event IDs from database
    platform_ids: dict[str, str] = {}

    # 1. Look up BetPawa event ID from Event table via EventBookmaker
    event_result = await db.execute(
        select(Event)
        .options(selectinload(Event.bookmaker_links))
        .where(Event.sportradar_id == sr_id)
    )
    event = event_result.scalar_one_or_none()

    if event:
        # Find BetPawa bookmaker link (bookmaker_id for BetPawa)
        for link in event.bookmaker_links:
            # BetPawa bookmaker_id is typically 1 or we can check by slug
            # For now, assume all bookmaker_links are BetPawa since Event table is BetPawa-centric
            platform_ids["betpawa"] = link.external_event_id
            break

    # 2. Look up competitor event IDs from CompetitorEvent table
    competitor_result = await db.execute(
        select(CompetitorEvent).where(CompetitorEvent.sportradar_id == sr_id)
    )
    competitor_events = competitor_result.scalars().all()

    for comp_event in competitor_events:
        if comp_event.source == "sportybet":
            platform_ids["sportybet"] = comp_event.external_id
        elif comp_event.source == "bet9ja":
            platform_ids["bet9ja"] = comp_event.external_id

    # 3. SportyBet uses sr:match: format if not found in CompetitorEvent
    if "sportybet" not in platform_ids:
        # SportyBet API accepts sr:match:{sr_id} format directly
        platform_ids["sportybet"] = f"sr:match:{sr_id}"

    # Validate at least one platform is available
    if not platform_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Event with SportRadar ID '{sr_id}' not found in any platform database",
        )

    log.info(
        "Starting single-event scrape",
        sr_id=sr_id,
        platforms=list(platform_ids.keys()),
    )

    # Get HTTP clients from app state
    clients = {
        "sportybet": SportyBetClient(request.app.state.sportybet_client),
        "betpawa": BetPawaClient(request.app.state.betpawa_client),
        "bet9ja": Bet9jaClient(request.app.state.bet9ja_client),
    }

    # Scrape all platforms in parallel
    async def scrape_platform(platform: str, platform_id: str):
        client = clients[platform]
        platform_start = time.perf_counter()
        try:
            result = await client.fetch_event(platform_id)
            elapsed_ms = int((time.perf_counter() - platform_start) * 1000)
            # Count markets from response if available
            markets_count = None
            if isinstance(result, dict):
                # Different platforms have different response structures
                if "markets" in result:
                    markets_count = len(result["markets"])
                elif "data" in result and isinstance(result["data"], dict):
                    if "markets" in result["data"]:
                        markets_count = len(result["data"]["markets"])
            return (platform, True, None, elapsed_ms, markets_count)
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - platform_start) * 1000)
            log.warning(
                "Platform scrape failed",
                platform=platform,
                sr_id=sr_id,
                error=str(e),
            )
            return (platform, False, str(e), elapsed_ms, None)

    # Execute all platform scrapes concurrently
    tasks = [scrape_platform(p, pid) for p, pid in platform_ids.items()]
    results = await asyncio.gather(*tasks)

    # Process results
    platforms_scraped: list[str] = []
    platforms_failed: list[str] = []
    platform_results: list[SingleEventPlatformResult] = []

    for platform, success, error, timing_ms, markets_count in results:
        platform_results.append(
            SingleEventPlatformResult(
                platform=platform,
                success=success,
                timing_ms=timing_ms,
                error=error,
                markets_count=markets_count,
            )
        )
        if success:
            platforms_scraped.append(platform)
        else:
            platforms_failed.append(platform)

    # Determine overall status
    if len(platforms_scraped) == len(platform_ids):
        status = "completed"
    elif len(platforms_scraped) > 0:
        status = "partial"
    else:
        status = "failed"

    total_timing_ms = int((time.perf_counter() - start_time) * 1000)

    log.info(
        "Single-event scrape complete",
        sr_id=sr_id,
        status=status,
        platforms_scraped=platforms_scraped,
        platforms_failed=platforms_failed,
        total_timing_ms=total_timing_ms,
    )

    return SingleEventScrapeResponse(
        sportradar_id=sr_id,
        status=status,
        platforms_scraped=platforms_scraped,
        platforms_failed=platforms_failed,
        platform_results=platform_results,
        total_timing_ms=total_timing_ms,
    )
