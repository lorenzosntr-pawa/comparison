"""Scrape API endpoints for triggering and monitoring scrape operations."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import ScrapeRequest, ScrapeResponse, ScrapeStatusResponse
from src.db.engine import get_db
from src.db.models.scrape import ScrapeRun, ScrapeStatus
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


@router.get("/{scrape_run_id}", response_model=ScrapeStatusResponse)
async def get_scrape_status(
    scrape_run_id: int,
    db: AsyncSession = Depends(get_db),
) -> ScrapeStatusResponse:
    """Get status of a scrape run by ID.

    Returns current status, counts, and timing information.
    """
    result = await db.execute(
        select(ScrapeRun).where(ScrapeRun.id == scrape_run_id)
    )
    scrape_run = result.scalar_one_or_none()

    if not scrape_run:
        raise HTTPException(status_code=404, detail="Scrape run not found")

    return ScrapeStatusResponse(
        scrape_run_id=scrape_run.id,
        status=scrape_run.status,
        started_at=scrape_run.started_at,
        completed_at=scrape_run.completed_at,
        events_scraped=scrape_run.events_scraped,
        events_failed=scrape_run.events_failed,
        platform_timings=scrape_run.platform_timings,
    )
