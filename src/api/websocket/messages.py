"""WebSocket message builders for typed JSON message construction.

All WebSocket messages follow a consistent shape:
    {"type": str, "timestamp": str, "data": dict}

These are lightweight dict builders (not Pydantic models) to keep
serialization fast for high-frequency broadcast scenarios.
"""

from datetime import datetime, timezone

from src.scraping.schemas import ScrapeProgress


def _utcnow_iso() -> str:
    """Return current UTC time as ISO 8601 string with Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _envelope(msg_type: str, data: dict) -> dict:
    """Wrap data in the standard message envelope.

    Args:
        msg_type: Message type discriminator.
        data: Payload specific to message type.

    Returns:
        Dict with type, timestamp, and data keys.
    """
    return {
        "type": msg_type,
        "timestamp": _utcnow_iso(),
        "data": data,
    }


def scrape_progress_message(progress: ScrapeProgress) -> dict:
    """Build a scrape_progress message from a ScrapeProgress model.

    Uses Pydantic's model_dump(mode="json") for consistent serialization,
    giving the same data shape the SSE endpoint sends.

    Args:
        progress: The ScrapeProgress Pydantic model instance.

    Returns:
        Typed message dict with type "scrape_progress".
    """
    return _envelope("scrape_progress", progress.model_dump(mode="json"))


def odds_update_message(
    event_ids: list[int], source: str, snapshot_count: int
) -> dict:
    """Build an odds_update notification message.

    Lightweight notification — frontend fetches full data from cache-first API.

    Args:
        event_ids: List of event IDs whose odds were updated.
        source: Bookmaker source ("betpawa", "sportybet", or "bet9ja").
        snapshot_count: Number of odds snapshots included.

    Returns:
        Typed message dict with type "odds_update".
    """
    return _envelope(
        "odds_update",
        {
            "event_ids": event_ids,
            "source": source,
            "snapshot_count": snapshot_count,
        },
    )


def connection_ack_message(topics: list[str]) -> dict:
    """Build a connection acknowledgment message.

    Sent to the client immediately after WebSocket connection is registered.

    Args:
        topics: List of topic names the client is subscribed to.

    Returns:
        Typed message dict with type "connection_ack".
    """
    return _envelope("connection_ack", {"topics": topics})


def pong_message() -> dict:
    """Build a pong response message.

    Sent in reply to a client "ping" message for keep-alive.

    Returns:
        Typed message dict with type "pong" and empty data.
    """
    return _envelope("pong", {})


def error_message(code: str, detail: str) -> dict:
    """Build an error message for the client.

    Args:
        code: Machine-readable error code (e.g. "invalid_topic").
        detail: Human-readable error description.

    Returns:
        Typed message dict with type "error".
    """
    return _envelope("error", {"code": code, "detail": detail})


def build_unmapped_alert(markets: list[dict]) -> dict:
    """Build WebSocket message for new unmapped markets.

    Sent when new unmapped markets are discovered during scraping.
    Allows real-time notification to users monitoring mapping coverage.

    Args:
        markets: List of dicts with source, externalMarketId, marketName.

    Returns:
        Typed message dict with type "unmapped_alert".
    """
    return _envelope(
        "unmapped_alert",
        {
            "count": len(markets),
            "markets": markets,
        },
    )
