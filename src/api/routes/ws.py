"""WebSocket endpoint for real-time client communication.

Provides a WebSocket connection at /ws (mounted at /api/ws via router prefix)
with topic-based subscriptions, ping/pong, and dynamic subscribe/unsubscribe.
"""

import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.websocket import ConnectionManager, connection_ack_message, pong_message
from src.api.websocket.messages import _utcnow_iso

log = structlog.get_logger("src.api.routes.ws")

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint with topic-based subscriptions.

    Provides real-time communication with clients via topic-based pub/sub.
    Clients can subscribe to specific topics to receive targeted updates.

    Args:
        websocket: FastAPI WebSocket connection.

    Query params:
        topics: Comma-separated topic names (e.g. ?topics=scrape_progress,odds_updates).
                Defaults to all topics if omitted.

    Client message types:
        - {"type": "ping"} -> responds with {"type": "pong", "timestamp": "..."}
        - {"type": "subscribe", "topics": [...]} -> adds topic subscriptions
        - {"type": "unsubscribe", "topics": [...]} -> removes topic subscriptions

    Server message types:
        - {"type": "connection_ack", "topics": [...]} -> sent on connect
        - {"type": "pong", "timestamp": "..."} -> response to ping
        - {"type": "subscription_update", "topics": [...]} -> after subscribe/unsubscribe
        - Topic-specific messages from broadcasters
    """
    # Accept the connection first
    await websocket.accept()

    # Parse optional topics query param
    topics_param = websocket.query_params.get("topics")
    topics: list[str] | None = None
    if topics_param:
        topics = [t.strip() for t in topics_param.split(",") if t.strip()]

    # Get ConnectionManager from app state
    manager: ConnectionManager = websocket.app.state.ws_manager

    try:
        # Register connection with manager
        await manager.connect(websocket, topics)

        # Determine actual subscribed topics for ack
        subscribed = manager._connections.get(websocket, set())

        # Send connection acknowledgment
        await websocket.send_json(connection_ack_message(sorted(subscribed)))

        # Receive loop
        while True:
            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError:
                log.debug("ws.malformed_message", client=str(websocket.client))
                continue

            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json(pong_message())

            elif msg_type == "subscribe":
                new_topics = data.get("topics", [])
                if isinstance(new_topics, list):
                    updated = manager.subscribe(websocket, new_topics)
                    await websocket.send_json(
                        {
                            "type": "subscription_update",
                            "topics": sorted(updated),
                            "timestamp": _utcnow_iso(),
                        }
                    )

            elif msg_type == "unsubscribe":
                rm_topics = data.get("topics", [])
                if isinstance(rm_topics, list):
                    updated = manager.unsubscribe(websocket, rm_topics)
                    await websocket.send_json(
                        {
                            "type": "subscription_update",
                            "topics": sorted(updated),
                            "timestamp": _utcnow_iso(),
                        }
                    )

            else:
                log.debug("ws.unknown_message_type", msg_type=msg_type)

    except WebSocketDisconnect:
        # Clean disconnect
        pass
    except Exception:
        log.exception("ws.error")
    finally:
        # Always clean up
        manager.disconnect(websocket)
