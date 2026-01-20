"""FastAPI application factory with async lifespan handler."""

from contextlib import asynccontextmanager
from typing import TypedDict

import httpx
from fastapi import FastAPI


# Default timeout for all HTTP clients (seconds)
DEFAULT_TIMEOUT = 30.0


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
    """Async lifespan context manager for HTTP client lifecycle.

    Creates AsyncClient instances at startup and closes them at shutdown.
    Clients are stored in app.state for dependency injection.
    """
    async with httpx.AsyncClient(
        base_url="https://www.sportybet.com",
        headers=SPORTYBET_HEADERS,
        timeout=DEFAULT_TIMEOUT,
    ) as sportybet_client:
        async with httpx.AsyncClient(
            base_url="https://www.betpawa.ng",
            headers=BETPAWA_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        ) as betpawa_client:
            async with httpx.AsyncClient(
                base_url="https://sports.bet9ja.com",
                headers=BET9JA_HEADERS,
                timeout=DEFAULT_TIMEOUT,
            ) as bet9ja_client:
                # Store clients in app state for dependency injection
                app.state.sportybet_client = sportybet_client
                app.state.betpawa_client = betpawa_client
                app.state.bet9ja_client = bet9ja_client

                yield


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

    return app
