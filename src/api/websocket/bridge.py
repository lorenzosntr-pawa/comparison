"""Bridge between ProgressBroadcaster/OddsCache and WebSocket clients.

Subscribes to a ProgressBroadcaster instance and forwards each
ScrapeProgress event as a WebSocket message to all clients subscribed
to the "scrape_progress" topic.  Runs as a background asyncio task
alongside the existing SSE streaming -- both are independent subscribers
of the same broadcaster.

Also provides a cache-to-WebSocket bridge for odds updates.
"""

import asyncio

import structlog

from src.api.websocket.manager import ConnectionManager
from src.api.websocket.messages import odds_update_message, scrape_progress_message
from src.caching.odds_cache import OddsCache
from src.scraping.broadcaster import ProgressBroadcaster

log = structlog.get_logger("src.api.websocket.bridge")


async def bridge_scrape_to_websocket(
    broadcaster: ProgressBroadcaster,
    ws_manager: ConnectionManager,
) -> None:
    """Forward ProgressBroadcaster events to WebSocket clients.

    Subscribes to the broadcaster's async generator and, for each
    ScrapeProgress event, builds a typed WebSocket message and
    broadcasts it to the "scrape_progress" topic.

    Designed to run as an ``asyncio.create_task`` -- it will exit
    gracefully when the broadcaster signals completion (generator ends)
    or when the task is cancelled.

    Args:
        broadcaster: The ProgressBroadcaster to subscribe to.
        ws_manager: The ConnectionManager handling WebSocket connections.
    """
    scrape_run_id = broadcaster.scrape_run_id
    events_forwarded = 0

    log.info("ws.bridge.started", scrape_run_id=scrape_run_id)

    try:
        async for progress in broadcaster.subscribe():
            message = scrape_progress_message(progress)
            await ws_manager.broadcast(message, topic="scrape_progress")
            events_forwarded += 1
    except Exception:
        log.exception(
            "ws.bridge.error",
            scrape_run_id=scrape_run_id,
            events_forwarded=events_forwarded,
        )
    else:
        log.info(
            "ws.bridge.ended",
            scrape_run_id=scrape_run_id,
            events_forwarded=events_forwarded,
        )


def create_cache_update_bridge(
    odds_cache: OddsCache,
    ws_manager: ConnectionManager,
) -> None:
    """Register OddsCache callback that broadcasts updates via WebSocket.

    Connects cache change notifications to WebSocket broadcasting so clients
    subscribed to "odds_updates" receive real-time notifications when odds data
    changes.

    Args:
        odds_cache: The OddsCache instance to monitor for changes.
        ws_manager: The ConnectionManager handling WebSocket connections.
    """

    def on_cache_update(event_ids: list[int], source: str) -> None:
        """Sync callback -- schedule async broadcast on the running loop."""
        try:
            loop = asyncio.get_running_loop()
            msg = odds_update_message(event_ids, source, len(event_ids))
            loop.create_task(_safe_broadcast(ws_manager, msg))
        except RuntimeError:
            # No running loop (shouldn't happen in FastAPI context)
            pass

    odds_cache.on_update(on_cache_update)
    log.info("ws.cache_bridge.registered")


async def _safe_broadcast(ws_manager: ConnectionManager, msg: dict) -> None:
    """Broadcast with error handling -- never crash the caller."""
    try:
        await ws_manager.broadcast(msg, topic="odds_updates")
    except Exception:
        log.exception("ws.cache_bridge.broadcast_error")
