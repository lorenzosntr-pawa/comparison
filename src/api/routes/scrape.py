"""Scrape API endpoints for triggering and monitoring scrape operations."""

from fastapi import APIRouter, HTTPException, Query, Request

from src.api.schemas import ScrapeRequest, ScrapeResponse, ScrapeStatusResponse
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.orchestrator import ScrapingOrchestrator

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("", response_model=ScrapeResponse)
async def trigger_scrape(
    request: Request,
    body: ScrapeRequest | None = None,
    detail: str = Query(
        default="summary",
        enum=["summary", "full"],
        description="Response detail level",
    ),
    timeout: int = Query(
        default=30,
        ge=5,
        le=300,
        description="Timeout per platform in seconds",
    ),
) -> ScrapeResponse:
    """Trigger a scrape operation across selected platforms.

    - **platforms**: Which platforms to scrape (default: all)
    - **detail**: "summary" for counts only, "full" to include all event data
    - **timeout**: Max seconds per platform (default 30, max 300)

    Returns scrape results with status and per-platform breakdown.
    Database persistence will be added in Plan 06.
    """
    # Build scraper clients from app state
    sportybet = SportyBetClient(request.app.state.sportybet_client)
    betpawa = BetPawaClient(request.app.state.betpawa_client)
    bet9ja = Bet9jaClient(request.app.state.bet9ja_client)

    orchestrator = ScrapingOrchestrator(sportybet, betpawa, bet9ja)

    # Execute scrape
    include_data = detail == "full"
    result = await orchestrator.scrape_all(
        platforms=body.platforms if body else None,
        sport_id=body.sport_id if body else None,
        competition_id=body.competition_id if body else None,
        include_data=include_data,
        timeout=float(timeout),
    )

    # Extract events from platform results if detail=full
    events = None
    if include_data:
        events = []
        for platform_result in result.platforms:
            if platform_result.events:
                events.extend(platform_result.events)

    return ScrapeResponse(
        scrape_run_id=0,  # Placeholder until DB integration in Plan 06
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
) -> ScrapeStatusResponse:
    """Get status of a scrape run by ID.

    Returns current status, counts, and optionally platform-level details.

    Note: This endpoint requires database integration (Plan 06).
    Currently returns 501 Not Implemented.
    """
    # Placeholder implementation until DB integration
    raise HTTPException(
        status_code=501,
        detail="DB integration pending - see Plan 06",
    )
