"""FastAPI application factory with async lifespan handler.

This module provides the main FastAPI application setup including:
- HTTP client lifecycle management for all betting platforms
- Scheduler initialization and configuration
- In-memory cache warmup and async write queue
- WebSocket connection manager and cache-to-websocket bridge
- Router registration for all API endpoints

The lifespan context manager ensures proper resource cleanup on shutdown.
"""

from contextlib import asynccontextmanager
from time import perf_counter
from typing import TypedDict

import httpx
import structlog
from fastapi import FastAPI

from src.api.routes.cleanup import router as cleanup_router
from src.api.routes.events import router as events_router
from src.api.routes.health import router as health_router
from src.api.routes.history import router as history_router
from src.api.routes.palimpsest import router as palimpsest_router
from src.api.routes.scheduler import router as scheduler_router
from src.api.routes.scrape import router as scrape_router
from src.api.routes.settings import router as settings_router
from src.api.routes.ws import router as ws_router
from src.api.websocket import ConnectionManager, create_cache_update_bridge
from src.caching.odds_cache import OddsCache
from src.caching.warmup import warm_cache_from_db
from src.db.engine import async_session_factory
from src.storage import AsyncWriteQueue
from src.scheduling.jobs import set_app_state
from src.scheduling.scheduler import (
    configure_scheduler,
    shutdown_scheduler,
    start_scheduler,
    sync_settings_on_startup,
)
from src.scheduling.stale_detection import recover_stale_runs_on_startup
from src.scraping.logging import configure_logging


# Default timeout for all HTTP clients (seconds)
DEFAULT_TIMEOUT = 30.0
"""Default HTTP request timeout in seconds for all platform clients."""

# Connection pool limits for concurrent scraping (Phase 56: increased for intra-batch concurrency)
# max_connections: total connections across all hosts
# max_keepalive_connections: connections to keep alive for reuse
# With 10 concurrent events x 3 platforms x ~3 connections + retries = ~90 peak, 200 max gives headroom
CONNECTION_LIMITS = httpx.Limits(
    max_connections=200,
    max_keepalive_connections=100,
)
"""HTTP connection pool limits for concurrent scraping operations."""


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
    """Application state containing HTTP clients for each platform.

    These clients are shared across all requests and managed by the
    lifespan context manager.

    Attributes:
        sportybet_client: HTTP client for SportyBet API.
        betpawa_client: HTTP client for BetPawa API.
        bet9ja_client: HTTP client for Bet9ja API.
    """

    sportybet_client: httpx.AsyncClient
    betpawa_client: httpx.AsyncClient
    bet9ja_client: httpx.AsyncClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async lifespan context manager for HTTP client and scheduler lifecycle.

    Creates AsyncClient instances at startup and closes them at shutdown.
    Clients are stored in app.state for dependency injection.
    Scheduler is configured and started after clients are available.

    Startup sequence:
    1. Create HTTP clients for all platforms
    2. Configure structured logging
    3. Initialize scheduler with app state access
    4. Recover stale runs from previous process
    5. Warm in-memory odds cache from database
    6. Start async write queue
    7. Initialize WebSocket connection manager
    8. Set up cache-to-WebSocket bridge

    Shutdown sequence:
    1. Drain and stop write queue
    2. Shutdown scheduler gracefully
    3. Close HTTP clients (handled by context managers)

    Args:
        app: The FastAPI application instance.

    Yields:
        None - resources are attached to app.state.
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
                # Configure structured logging (dev mode by default)
                configure_logging(json_output=False)

                # Store clients in app state for dependency injection
                app.state.sportybet_client = sportybet_client
                app.state.betpawa_client = betpawa_client
                app.state.bet9ja_client = bet9ja_client

                # Initialize scheduler with app state access
                set_app_state(app.state)

                # Recover any runs left in RUNNING from previous process
                recovered = await recover_stale_runs_on_startup()

                configure_scheduler()
                start_scheduler()

                # Sync scheduler interval from stored settings
                await sync_settings_on_startup()

                # --- In-memory odds cache warmup ---
                log = structlog.get_logger("src.api.app")
                odds_cache = OddsCache()
                app.state.odds_cache = odds_cache

                t0 = perf_counter()
                async with async_session_factory() as db:
                    warmup_stats = await warm_cache_from_db(odds_cache, db)
                warmup_ms = (perf_counter() - t0) * 1000
                log.info(
                    "cache.warmup.done",
                    warmup_ms=round(warmup_ms, 1),
                    **warmup_stats,
                )

                # --- Async write queue ---
                t0 = perf_counter()
                write_queue = AsyncWriteQueue(
                    session_factory=async_session_factory,
                    maxsize=50,
                )
                await write_queue.start()
                app.state.write_queue = write_queue
                wq_ms = (perf_counter() - t0) * 1000
                log.info(
                    "write_queue_started",
                    startup_ms=round(wq_ms, 1),
                )

                # --- WebSocket connection manager ---
                ws_manager = ConnectionManager()
                app.state.ws_manager = ws_manager
                log.info("ws_manager_ready")

                # --- Cache-to-WebSocket bridge ---
                create_cache_update_bridge(odds_cache, ws_manager)
                log.info("ws.cache_bridge.ready")

                yield

                # --- Shutdown ---
                # Stop write queue first (drains remaining items)
                await write_queue.stop()

                # Shutdown scheduler gracefully
                shutdown_scheduler()


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Creates the FastAPI app with lifespan handler and registers all
    API routers under the /api prefix.

    Returns:
        Configured FastAPI application instance ready to serve requests.
    """
    app = FastAPI(
        lifespan=lifespan,
        title="Betpawa Odds Comparison API",
        version="0.1.0",
    )

    # Include routers with /api prefix
    app.include_router(cleanup_router, prefix="/api")
    app.include_router(events_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(history_router, prefix="/api")
    app.include_router(palimpsest_router, prefix="/api")
    app.include_router(scheduler_router, prefix="/api")
    app.include_router(scrape_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(ws_router, prefix="/api")

    return app
