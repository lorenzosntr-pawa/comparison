"""FastAPI application factory with async lifespan handler."""

from contextlib import asynccontextmanager
from typing import TypedDict

import httpx
from fastapi import FastAPI

from api.routes.events import router as events_router
from api.routes.health import router as health_router
from api.routes.scheduler import router as scheduler_router
from api.routes.scrape import router as scrape_router
from src.scheduling.jobs import set_app_state
from src.scheduling.scheduler import (
    configure_scheduler,
    shutdown_scheduler,
    start_scheduler,
)


# Default timeout for all HTTP clients (seconds)
DEFAULT_TIMEOUT = 30.0

# Connection pool limits for concurrent scraping
# max_connections: total connections across all hosts
# max_keepalive_connections: connections to keep alive for reuse
CONNECTION_LIMITS = httpx.Limits(
    max_connections=100,
    max_keepalive_connections=50,
)


# Platform-specific headers (copied from scraper configs to avoid import issues)
SPORTYBET_HEADERS = {
    "accept": "*/*",
    "accept-language": "en",
    "clientid": "web",
    "operid": "2",
    "platform": "web",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
}

BETPAWA_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "devicetype": "web",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "x-pawa-brand": "betpawa-nigeria",
}

BET9JA_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
}


class AppState(TypedDict):
    """Application state containing HTTP clients for each platform."""

    sportybet_client: httpx.AsyncClient
    betpawa_client: httpx.AsyncClient
    bet9ja_client: httpx.AsyncClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async lifespan context manager for HTTP client and scheduler lifecycle.

    Creates AsyncClient instances at startup and closes them at shutdown.
    Clients are stored in app.state for dependency injection.
    Scheduler is configured and started after clients are available.
    """
    async with httpx.AsyncClient(
        base_url="https://www.sportybet.com",
        headers=SPORTYBET_HEADERS,
        timeout=DEFAULT_TIMEOUT,
        limits=CONNECTION_LIMITS,
    ) as sportybet_client:
        async with httpx.AsyncClient(
            base_url="https://www.betpawa.ng",
            headers=BETPAWA_HEADERS,
            timeout=DEFAULT_TIMEOUT,
            limits=CONNECTION_LIMITS,
        ) as betpawa_client:
            async with httpx.AsyncClient(
                base_url="https://sports.bet9ja.com",
                headers=BET9JA_HEADERS,
                timeout=DEFAULT_TIMEOUT,
                limits=CONNECTION_LIMITS,
            ) as bet9ja_client:
                # Store clients in app state for dependency injection
                app.state.sportybet_client = sportybet_client
                app.state.betpawa_client = betpawa_client
                app.state.bet9ja_client = bet9ja_client

                # Initialize scheduler with app state access
                set_app_state(app.state)
                configure_scheduler()
                start_scheduler()

                yield

                # Shutdown scheduler gracefully
                shutdown_scheduler()


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        lifespan=lifespan,
        title="Betpawa Odds Comparison API",
        version="0.1.0",
    )

    # Include routers
    app.include_router(events_router)
    app.include_router(health_router)
    app.include_router(scheduler_router)
    app.include_router(scrape_router)

    return app
