"""WebSocket connection manager with topic-based subscriptions.

Manages WebSocket connections and broadcasts messages to subscribers
grouped by topic. Designed for real-time odds updates and scrape progress.
"""

import asyncio

import structlog
from starlette.websockets import WebSocket, WebSocketDisconnect

log = structlog.get_logger("src.api.websocket.manager")

# Predefined topics (extensible — any string works as a topic)
TOPICS = {"scrape_progress", "odds_updates"}


class ConnectionManager:
    """Manages WebSocket connections with topic-based pub/sub.

    Each connection subscribes to one or more topics. Messages are
    broadcast to all subscribers of a given topic.

    Thread-safe via asyncio.Lock for connect/disconnect operations.
    Broadcast uses snapshot iteration to avoid mutation during send.

    Attributes:
        _connections: Mapping of WebSocket to subscribed topic names.
        _topics: Reverse index mapping topic name to subscribed WebSockets.
        _lock: Asyncio lock for thread-safe connect/disconnect.
    """

    def __init__(self) -> None:
        """Initialize the connection manager with empty connection tracking."""
        # WebSocket -> set of subscribed topic names
        self._connections: dict[WebSocket, set[str]] = {}
        # Topic name -> set of subscribed WebSockets (reverse index)
        self._topics: dict[str, set[WebSocket]] = {}
        # Lock for connect/disconnect to prevent race conditions
        self._lock = asyncio.Lock()

    async def connect(
        self, websocket: WebSocket, topics: list[str] | None = None
    ) -> None:
        """Accept a WebSocket connection and register with topics.

        Args:
            websocket: The WebSocket connection to register.
            topics: List of topics to subscribe to. If None, subscribes
                    to all predefined topics.
        """
        if topics is None:
            resolved_topics = set(TOPICS)
        else:
            resolved_topics = set(topics) & TOPICS  # Only allow known topics
            if not resolved_topics:
                resolved_topics = set(TOPICS)  # Fall back to all if none valid

        async with self._lock:
            self._connections[websocket] = resolved_topics
            for topic in resolved_topics:
                if topic not in self._topics:
                    self._topics[topic] = set()
                self._topics[topic].add(websocket)

        log.info(
            "ws.connect",
            topics=sorted(resolved_topics),
            total_connections=self.active_count,
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket from all data structures.

        Synchronous — no await needed, just dict cleanup.

        Args:
            websocket: The WebSocket connection to remove.
        """
        topics = self._connections.pop(websocket, set())
        for topic in topics:
            topic_set = self._topics.get(topic)
            if topic_set is not None:
                topic_set.discard(websocket)
                if not topic_set:
                    del self._topics[topic]

        log.info("ws.disconnect", total_connections=self.active_count)

    async def broadcast(self, message: dict, topic: str) -> None:
        """Send a JSON message to all subscribers of a topic.

        Dead connections are silently removed after iteration.

        Args:
            message: JSON-serializable dict to send.
            topic: The topic to broadcast to.
        """
        # Snapshot to avoid mutation during iteration
        subscribers = set(self._topics.get(topic, set()))
        if not subscribers:
            return

        dead: list[WebSocket] = []
        for ws in subscribers:
            try:
                await ws.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                dead.append(ws)

        # Clean up dead connections outside iteration
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_all(self, message: dict) -> None:
        """Send a JSON message to every connected client regardless of topic.

        Args:
            message: JSON-serializable dict to send.
        """
        # Snapshot all connections
        all_ws = set(self._connections.keys())
        if not all_ws:
            return

        dead: list[WebSocket] = []
        for ws in all_ws:
            try:
                await ws.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                dead.append(ws)

        # Clean up dead connections outside iteration
        for ws in dead:
            self.disconnect(ws)

    def subscribe(self, websocket: WebSocket, topics: list[str]) -> set[str]:
        """Add topic subscriptions for an existing connection.

        Args:
            websocket: The connected WebSocket.
            topics: Topics to add.

        Returns:
            The updated set of subscribed topics.
        """
        if websocket not in self._connections:
            return set()

        valid_topics = set(topics) & TOPICS
        current = self._connections[websocket]
        for topic in valid_topics:
            if topic not in current:
                current.add(topic)
                if topic not in self._topics:
                    self._topics[topic] = set()
                self._topics[topic].add(websocket)

        return current

    def unsubscribe(self, websocket: WebSocket, topics: list[str]) -> set[str]:
        """Remove topic subscriptions for an existing connection.

        Args:
            websocket: The connected WebSocket.
            topics: Topics to remove.

        Returns:
            The updated set of subscribed topics.
        """
        if websocket not in self._connections:
            return set()

        current = self._connections[websocket]
        for topic in topics:
            if topic in current:
                current.discard(topic)
                topic_set = self._topics.get(topic)
                if topic_set is not None:
                    topic_set.discard(websocket)
                    if not topic_set:
                        del self._topics[topic]

        return current

    @property
    def active_count(self) -> int:
        """Number of connected clients.

        Returns:
            Total count of active WebSocket connections.
        """
        return len(self._connections)

    @property
    def topic_counts(self) -> dict[str, int]:
        """Subscriber count per topic.

        Returns:
            Dict mapping topic name to subscriber count.
        """
        return {topic: len(subs) for topic, subs in self._topics.items()}
