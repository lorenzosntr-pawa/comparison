"""Bridge between ProgressBroadcaster and WebSocket clients.

Subscribes to a ProgressBroadcaster instance and forwards each
ScrapeProgress event as a WebSocket message to all clients subscribed
to the "scrape_progress" topic.  Runs as a background asyncio task
alongside the existing SSE streaming -- both are independent subscribers
of the same broadcaster.
"""

import structlog

from src.api.websocket.manager import ConnectionManager
from src.api.websocket.messages import scrape_progress_message
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
