"""Async HTTP client for BetPawa API.

Provides the BetPawaClient class for fetching events and odds from the
BetPawa Nigeria platform (www.betpawa.ng).

BetPawa is the primary/canonical platform in this system. All other
platforms' odds are mapped to BetPawa's market format for comparison.

Response Structure:
    - Event ID is in "id" field
    - SportRadar ID in "widgets" array where type="SPORTRADAR"
    - Markets in "markets" array with nested "row" containing "prices"
    - Competition/region info for tournament matching

Headers:
    Requires "x-pawa-brand: betpawa-nigeria" header for API access.
    Uses standard browser User-Agent for compatibility.

Retry Behavior:
    All methods use @retry decorator with exponential backoff (max 3 attempts).
    Returns 404 for invalid event IDs (raises InvalidEventIdError).
"""

import json
from urllib.parse import quote

import httpx

from src.scraping.clients.base import create_retry_decorator
from src.scraping.exceptions import ApiError, InvalidEventIdError, NetworkError

# BetPawa API configuration
BASE_URL = "https://www.betpawa.ng"
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "devicetype": "web",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "x-pawa-brand": "betpawa-nigeria",
}

# Create retry decorator
_retry = create_retry_decorator()


def _validate_response_structure(data: dict) -> None:
    """Validate API response structure.

    Args:
        data: Parsed API response.

    Raises:
        ApiError: If critical keys are missing.
    """
    if not isinstance(data, dict):
        raise ApiError(
            f"Expected dict response, got {type(data).__name__}",
            details={"response": data},
        )

    if "id" not in data:
        raise ApiError(
            "Response missing 'id' key",
            details={"response": data},
        )


class BetPawaClient:
    """Async HTTP client for BetPawa API."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        """Initialize with an async HTTP client.

        Args:
            client: Configured httpx.AsyncClient instance.
        """
        self._client = client

    @_retry
    async def fetch_event(self, event_id: str) -> dict:
        """Fetch event data from BetPawa API.

        Args:
            event_id: BetPawa event ID (e.g., "32299257").

        Returns:
            Full API response dict containing event, markets, widgets.

        Raises:
            InvalidEventIdError: If the API returns 404.
            NetworkError: If a connection or timeout error occurs.
            ApiError: If response structure is invalid.
        """
        try:
            response = await self._client.get(
                f"{BASE_URL}/api/sportsbook/v3/events/{event_id}",
                headers=HEADERS,
            )

            if response.status_code == 404:
                raise InvalidEventIdError(
                    event_id=event_id,
                    message="Event not found",
                )

            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise NetworkError(
                f"Network error fetching event {event_id}: {e}",
                cause=e,
            ) from e

        data = response.json()
        _validate_response_structure(data)

        return data

    @_retry
    async def fetch_events(
        self,
        competition_id: str,
        state: str = "UPCOMING",
        page: int = 1,
        size: int = 100,
    ) -> dict:
        """Fetch events list for a competition.

        Args:
            competition_id: Competition ID (e.g., "11965" for Premier League).
            state: Event state - "UPCOMING" or "LIVE".
            page: Page number (1-indexed).
            size: Number of events per page.

        Returns:
            Full API response with events list and pagination.

        Raises:
            NetworkError: If a connection or timeout error occurs.
            ApiError: If response structure is invalid.
        """
        query = {
            "queries": [
                {
                    "query": {
                        "eventType": state,
                        "categories": ["2"],  # Football
                        "zones": {"competitions": [competition_id]},
                        "hasOdds": True,
                    },
                    "view": {},
                    "skip": (page - 1) * size,
                    "take": size,
                }
            ]
        }

        q_param = quote(json.dumps(query))

        try:
            response = await self._client.get(
                f"{BASE_URL}/api/sportsbook/v3/events/lists/by-queries?q={q_param}",
                headers=HEADERS,
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise NetworkError(
                f"Network error fetching events for competition {competition_id}: {e}",
                cause=e,
            ) from e

        data = response.json()

        if not isinstance(data, dict):
            raise ApiError(
                f"Expected dict response for events query, got {type(data).__name__}",
                details={"response": data},
            )

        return data

    @_retry
    async def fetch_categories(self, category_id: str = "2") -> dict:
        """Fetch categories list with regions and competitions.

        Args:
            category_id: Category ID (default "2" for Football).

        Returns:
            Categories/regions structure.

        Raises:
            NetworkError: If a connection or timeout error occurs.
            ApiError: If response structure is invalid.
        """
        try:
            response = await self._client.get(
                f"{BASE_URL}/api/sportsbook/v3/categories/list/{category_id}",
                headers=HEADERS,
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise NetworkError(
                f"Network error fetching categories: {e}",
                cause=e,
            ) from e

        data = response.json()

        if not isinstance(data, dict):
            raise ApiError(
                f"Expected dict response for categories, got {type(data).__name__}",
                details={"response": data},
            )

        return data

    async def check_health(self) -> bool:
        """Check if the BetPawa API is reachable.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            response = await self._client.get(
                f"{BASE_URL}/api/sportsbook/v3/categories/list/2",
                headers=HEADERS,
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False
