"""Scrape API endpoints for triggering and monitoring scrape operations."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from src.api.schemas import (
    ScrapeErrorResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeRunResponse,
    ScrapeStatsResponse,
    ScrapeStatusResponse,
)
from src.db.engine import get_db
from src.db.models.scrape import ScrapeError, ScrapeRun, ScrapeStatus
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
        try:
            async for progress in orchestrator.scrape_with_progress(
                timeout=float(timeout),
                scrape_run_id=scrape_run.id,
                db=db,
            ):
                if await request.is_disconnected():
                    break
                yield f"data: {progress.model_dump_json()}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'phase': 'failed', 'message': str(e)})}\n\n"
        finally:
            # Update ScrapeRun on completion
            scrape_run.status = ScrapeStatus.COMPLETED
            scrape_run.completed_at = datetime.utcnow()
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
