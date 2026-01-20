"""FastAPI dependencies for HTTP clients and database sessions."""

import httpx
from fastapi import Request

from db.engine import get_db


__all__ = ["get_sportybet_client", "get_betpawa_client", "get_bet9ja_client", "get_db"]


def get_sportybet_client(request: Request) -> httpx.AsyncClient:
    """Get SportyBet HTTP client from app state.

    Args:
        request: FastAPI request object.

    Returns:
        Configured httpx.AsyncClient for SportyBet API.
    """
    return request.app.state.sportybet_client


def get_betpawa_client(request: Request) -> httpx.AsyncClient:
    """Get BetPawa HTTP client from app state.

    Args:
        request: FastAPI request object.

    Returns:
        Configured httpx.AsyncClient for BetPawa API.
    """
    return request.app.state.betpawa_client


def get_bet9ja_client(request: Request) -> httpx.AsyncClient:
    """Get Bet9ja HTTP client from app state.

    Args:
        request: FastAPI request object.

    Returns:
        Configured httpx.AsyncClient for Bet9ja API.
    """
    return request.app.state.bet9ja_client
