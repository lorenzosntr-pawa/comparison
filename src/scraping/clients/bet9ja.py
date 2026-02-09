"""Async HTTP client for Bet9ja API.

Provides the Bet9jaClient class for fetching events and odds from the
Bet9ja sports betting platform (sports.bet9ja.com).

Rate Limiting:
    Bet9ja is more sensitive to request rates than other platforms.
    The EventCoordinator applies a 25ms delay after each Bet9ja request
    and limits concurrency to 15 parallel requests (vs 50 for others).

Response Structure:
    - Uses "R" field for result code: "OK" or "D" = success, "E" = not found
    - Event data nested in "D" payload
    - Odds in "D.O" dict with keys like "S_1X2_1", "S_OU_2.5_O", etc.
    - SportRadar ID in "EXTID" field for cross-platform matching

Retry Behavior:
    All methods use @retry decorator with exponential backoff (max 3 attempts).
    Retries on network errors and timeouts, not on 404/invalid event.
"""

import httpx

from src.scraping.clients.base import create_retry_decorator
from src.scraping.exceptions import ApiError, InvalidEventIdError, NetworkError

# Bet9ja API configuration
BASE_URL = "https://sports.bet9ja.com"
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
}

# Create retry decorator
_retry = create_retry_decorator()


def _validate_response_success(data: dict, context: str) -> None:
    """Validate API response has success code.

    Args:
        data: Parsed API response.
        context: Context for error message (e.g., "event 123").

    Raises:
        ApiError: If response is not a dict or R != "OK".
    """
    if not isinstance(data, dict):
        raise ApiError(
            f"Expected dict response for {context}, got {type(data).__name__}",
            details={"response": data},
        )

    result_code = data.get("R")
    if result_code != "OK":
        raise ApiError(
            f"API returned R='{result_code}' for {context}, expected 'OK'",
            details={"response": data},
        )


class Bet9jaClient:
    """Async HTTP client for Bet9ja API."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        """Initialize with an async HTTP client.

        Args:
            client: Configured httpx.AsyncClient instance.
        """
        self._client = client

    @_retry
    async def fetch_event(self, event_id: str) -> dict:
        """Fetch full event details from Bet9ja API.

        Args:
            event_id: Bet9ja event ID (e.g., "707096003").

        Returns:
            The D payload containing event details and odds dict.

        Raises:
            InvalidEventIdError: If the event is not found.
            NetworkError: If a connection or timeout error occurs.
            ApiError: If response structure is invalid.
        """
        try:
            response = await self._client.get(
                f"{BASE_URL}/desktop/feapi/PalimpsestAjax/GetEvent",
                params={
                    "EVENTID": event_id,
                    "v_cache_version": "1.301.2.225",
                },
                headers=HEADERS,
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise NetworkError(
                f"Network error fetching event {event_id}: {e}",
                cause=e,
            ) from e

        data = response.json()

        # Check for "D" result code which indicates success for single event
        if not isinstance(data, dict):
            raise ApiError(
                f"Expected dict response for event {event_id}, got {type(data).__name__}",
                details={"response": data},
            )

        result_code = data.get("R")
        if result_code in ("D", "OK"):
            # Success - return the D payload (GetEvent returns "D" or "OK")
            d_data = data.get("D")
            if not isinstance(d_data, dict):
                raise ApiError(
                    f"Expected 'D' to be dict for event {event_id}, got {type(d_data).__name__ if d_data else 'None'}",
                    details={"response": data},
                )
            return d_data
        elif result_code == "E":
            # Event not found
            raise InvalidEventIdError(
                event_id=event_id,
                message=f"Event {event_id} not found (R='E')",
            )
        else:
            raise ApiError(
                f"API returned R='{result_code}' for event {event_id}, expected 'D' or 'OK'",
                details={"response": data},
            )

    @_retry
    async def fetch_events(self, tournament_id: str) -> list[dict]:
        """Fetch events for a tournament from Bet9ja API.

        Args:
            tournament_id: Tournament/group ID from navigation (e.g., "170880").

        Returns:
            List of event dicts from D.E array.

        Raises:
            NetworkError: If a connection or timeout error occurs.
            ApiError: If response structure is invalid.
        """
        try:
            response = await self._client.get(
                f"{BASE_URL}/desktop/feapi/PalimpsestAjax/GetEventsInGroupV2",
                params={
                    "GROUPID": tournament_id,
                    "DISP": "0",
                    "GROUPMARKETID": "1",
                    "v_cache_version": "1.301.2.225",
                },
                headers=HEADERS,
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise NetworkError(
                f"Network error fetching events for tournament {tournament_id}: {e}",
                cause=e,
            ) from e

        data = response.json()
        _validate_response_success(data, f"tournament {tournament_id}")

        d_data = data.get("D")
        if not isinstance(d_data, dict):
            raise ApiError(
                f"Expected 'D' to be dict for tournament {tournament_id}, got {type(d_data).__name__ if d_data else 'None'}",
                details={"response": data},
            )

        events_data = d_data.get("E", [])
        if not isinstance(events_data, list):
            raise ApiError(
                f"Expected 'D.E' to be list for tournament {tournament_id}, got {type(events_data).__name__}",
                details={"response": data},
            )

        return events_data

    @_retry
    async def fetch_sports(self) -> dict:
        """Fetch sports data from Bet9ja API for connectivity test.

        Returns:
            Full API response dict containing D.PAL structure.

        Raises:
            NetworkError: If a connection or timeout error occurs.
            ApiError: If response structure is invalid.
        """
        try:
            response = await self._client.get(
                f"{BASE_URL}/desktop/feapi/PalimpsestAjax/GetSports",
                params={
                    "DISP": "0",
                    "v_cache_version": "1.301.2.225",
                },
                headers=HEADERS,
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise NetworkError(
                f"Network error fetching sports: {e}",
                cause=e,
            ) from e

        data = response.json()
        _validate_response_success(data, "sports")

        d_data = data.get("D")
        if not isinstance(d_data, dict):
            raise ApiError(
                f"Expected 'D' to be dict for sports, got {type(d_data).__name__ if d_data else 'None'}",
                details={"response": data},
            )

        pal_data = d_data.get("PAL")
        if not isinstance(pal_data, dict):
            raise ApiError(
                f"Expected 'D.PAL' to be dict for sports, got {type(pal_data).__name__ if pal_data else 'None'}",
                details={"response": data},
            )

        return data

    async def check_health(self) -> bool:
        """Check if the Bet9ja API is reachable.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            response = await self._client.get(
                f"{BASE_URL}/desktop/feapi/PalimpsestAjax/GetSports",
                params={"DISP": "0", "v_cache_version": "1.301.2.225"},
                headers=HEADERS,
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False
