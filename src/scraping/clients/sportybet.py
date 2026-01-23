"""Async HTTP client for SportyBet API."""

import time

import httpx

from src.scraping.clients.base import create_retry_decorator
from src.scraping.exceptions import ApiError, InvalidEventIdError, NetworkError

# SportyBet API configuration
BASE_URL = "https://www.sportybet.com"
HEADERS = {
    "accept": "*/*",
    "accept-language": "en",
    "clientid": "web",
    "operid": "2",
    "platform": "web",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
}

# Create retry decorator
_retry = create_retry_decorator()


def _validate_response_structure(data: dict, event_id: str) -> None:
    """Validate API response structure.

    Args:
        data: Parsed API response.
        event_id: Event ID for error context.

    Raises:
        ApiError: If 'data' key is missing.
    """
    if "data" not in data:
        raise ApiError(
            f"Response missing 'data' key for event {event_id}",
            details={"response": data},
        )


class SportyBetClient:
    """Async HTTP client for SportyBet API."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        """Initialize with an async HTTP client.

        Args:
            client: Configured httpx.AsyncClient instance.
        """
        self._client = client

    @_retry
    async def fetch_event(self, event_id: str) -> dict:
        """Fetch event data from SportyBet API.

        Args:
            event_id: SportRadar event ID (e.g., "sr:match:61300947").

        Returns:
            Inner event data payload (data["data"]).

        Raises:
            InvalidEventIdError: If the API returns a non-success bizCode.
            NetworkError: If a connection or timeout error occurs.
            ApiError: If response structure is invalid.
        """
        params = {
            "eventId": event_id,
            "productId": "3",
            "_t": str(int(time.time() * 1000)),
        }

        try:
            response = await self._client.get(
                f"{BASE_URL}/api/ng/factsCenter/event",
                params=params,
                headers=HEADERS,
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise NetworkError(
                f"Network error fetching event {event_id}: {e}",
                cause=e,
            ) from e

        data = response.json()

        if data.get("bizCode") != 10000:
            raise InvalidEventIdError(
                event_id=event_id,
                message=f"bizCode={data.get('bizCode')}: {data.get('message', 'Unknown error')}",
            )

        _validate_response_structure(data, event_id)

        return data["data"]

    @_retry
    async def fetch_tournaments(self, sport_id: str = "sr:sport:1") -> dict:
        """Fetch tournament hierarchy from SportyBet API.

        Args:
            sport_id: SportRadar sport ID (default: sr:sport:1 for football).

        Returns:
            Full API response with sportList containing categories and tournaments.

        Raises:
            NetworkError: If a connection or timeout error occurs.
            ApiError: If response structure is invalid or bizCode != 10000.
        """
        params = {
            "sportId": sport_id,
            "timeline": "",
            "productId": "3",
            "_t": str(int(time.time() * 1000)),
        }

        try:
            response = await self._client.get(
                f"{BASE_URL}/api/ng/factsCenter/popularAndSportList",
                params=params,
                headers=HEADERS,
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise NetworkError(
                f"Network error fetching tournaments: {e}",
                cause=e,
            ) from e

        data = response.json()

        if data.get("bizCode") != 10000:
            raise ApiError(
                f"bizCode={data.get('bizCode')}: {data.get('message', 'Unknown error')}",
                details={"response": data},
            )

        return data

    async def check_health(self) -> bool:
        """Check if the SportyBet API is reachable.

        Uses the event endpoint with a dummy ID - any response (including
        404/400 for invalid event) indicates the API is reachable.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            response = await self._client.get(
                f"{BASE_URL}/api/ng/factsCenter/event",
                params={"eventId": "sr:match:1", "productId": "3"},
                headers=HEADERS,
                timeout=5.0,
            )
            # Any response (even error) means API is reachable
            return response.status_code in (200, 400, 404)
        except Exception:
            return False
