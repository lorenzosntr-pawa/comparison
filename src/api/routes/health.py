"""Health check endpoint with platform and database connectivity verification."""

import asyncio
import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import HealthResponse, PlatformHealth
from src.db.engine import get_db
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.schemas import Platform

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """Check connectivity to all platforms and database.

    Returns overall status:
    - "healthy": All platforms and database reachable
    - "degraded": Some platforms unreachable but at least one works
    - "unhealthy": No platforms reachable or database down
    """
    # Check database
    db_status = await _check_database(db)

    # Build clients from app state
    sportybet = SportyBetClient(request.app.state.sportybet_client)
    betpawa = BetPawaClient(request.app.state.betpawa_client)
    bet9ja = Bet9jaClient(request.app.state.bet9ja_client)

    # Check platforms concurrently
    platform_checks = await asyncio.gather(
        _check_platform(Platform.SPORTYBET, sportybet),
        _check_platform(Platform.BETPAWA, betpawa),
        _check_platform(Platform.BET9JA, bet9ja),
        return_exceptions=True,
    )

    platforms = []
    for idx, result in enumerate(platform_checks):
        if isinstance(result, Exception):
            # Shouldn't happen since _check_platform catches exceptions
            platform = [Platform.SPORTYBET, Platform.BETPAWA, Platform.BET9JA][idx]
            platforms.append(
                PlatformHealth(
                    platform=platform,
                    status="unhealthy",
                    error=str(result),
                )
            )
        else:
            platforms.append(result)

    # Determine overall status
    healthy_count = sum(1 for p in platforms if p.status == "healthy")
    if db_status == "disconnected":
        overall = "unhealthy"
    elif healthy_count == len(platforms):
        overall = "healthy"
    elif healthy_count > 0:
        overall = "degraded"
    else:
        overall = "unhealthy"

    return HealthResponse(status=overall, database=db_status, platforms=platforms)


async def _check_database(db: AsyncSession) -> str:
    """Check database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return "connected"
    except Exception:
        return "disconnected"


async def _check_platform(platform: Platform, client) -> PlatformHealth:
    """Check a single platform's health."""
    start = time.perf_counter()
    try:
        healthy = await client.check_health()
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return PlatformHealth(
            platform=platform,
            status="healthy" if healthy else "unhealthy",
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return PlatformHealth(
            platform=platform,
            status="unhealthy",
            response_time_ms=elapsed_ms,
            error=str(e),
        )
