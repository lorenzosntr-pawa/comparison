"""Progress broadcaster for real-time scrape progress updates.

This module implements the pub/sub pattern for streaming scrape progress
to WebSocket clients. It provides:

- ProgressBroadcaster: Per-run broadcaster with subscriber management
- ProgressRegistry: Global singleton registry of active broadcasters

Architecture:
    Scheduled jobs -> ProgressBroadcaster.publish() -> Queue per subscriber
    WebSocket endpoint -> ProgressBroadcaster.subscribe() -> AsyncGenerator

Thread Safety:
    Uses asyncio.Lock for subscriber list mutations. Safe for single-writer
    (scheduled job) / multi-reader (multiple WebSocket clients) pattern.

Example:
    # In scheduled job
    broadcaster = progress_registry.create_broadcaster(scrape_run_id)
    await broadcaster.publish(progress_event)

    # In WebSocket endpoint
    broadcaster = progress_registry.get_broadcaster(scrape_run_id)
    async for progress in broadcaster.subscribe():
        await websocket.send_json(progress.model_dump())
"""

import asyncio
from collections.abc import AsyncGenerator

from src.scraping.schemas import ScrapeProgress


class ProgressBroadcaster:
    """Broadcasts scrape progress to multiple subscribers.

    Thread-safe progress state management with pub/sub pattern.
    One broadcaster instance per scrape run.
    """

    def __init__(self, scrape_run_id: int) -> None:
        """Initialize broadcaster for a scrape run.

        Args:
            scrape_run_id: ID of the scrape run to track.
        """
        self.scrape_run_id = scrape_run_id
        self._subscribers: list[asyncio.Queue[ScrapeProgress | None]] = []
        self._latest_progress: ScrapeProgress | None = None
        self._completed = False
        self._lock = asyncio.Lock()

    async def publish(self, progress: ScrapeProgress) -> None:
        """Publish a progress update to all subscribers.

        Args:
            progress: The progress update to broadcast.
        """
        async with self._lock:
            self._latest_progress = progress

            # Check if this is the final update
            if progress.phase in ("completed", "failed") and progress.platform is None:
                self._completed = True

            # Send to all subscribers
            for queue in self._subscribers:
                try:
                    queue.put_nowait(progress)
                except asyncio.QueueFull:
                    # Drop oldest if queue is full
                    try:
                        queue.get_nowait()
                        queue.put_nowait(progress)
                    except asyncio.QueueEmpty:
                        pass

    async def subscribe(self) -> AsyncGenerator[ScrapeProgress, None]:
        """Subscribe to progress updates.

        Yields progress updates as they arrive. Also yields the latest
        progress immediately if available (for late subscribers).

        Yields:
            ScrapeProgress updates.
        """
        queue: asyncio.Queue[ScrapeProgress | None] = asyncio.Queue(maxsize=50)

        async with self._lock:
            self._subscribers.append(queue)

            # Send latest progress immediately (catch up)
            if self._latest_progress:
                await queue.put(self._latest_progress)

            # If already completed, signal end
            if self._completed:
                await queue.put(None)

        try:
            while True:
                progress = await queue.get()
                if progress is None:
                    break
                yield progress

                # Check for completion
                if progress.phase in ("completed", "failed") and progress.platform is None:
                    break
        finally:
            async with self._lock:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)

    async def close(self) -> None:
        """Close the broadcaster and notify all subscribers."""
        async with self._lock:
            self._completed = True
            for queue in self._subscribers:
                try:
                    queue.put_nowait(None)
                except asyncio.QueueFull:
                    pass

    @property
    def subscriber_count(self) -> int:
        """Get the number of active subscribers."""
        return len(self._subscribers)

    @property
    def is_completed(self) -> bool:
        """Check if the scrape has completed."""
        return self._completed

    @property
    def latest_progress(self) -> ScrapeProgress | None:
        """Get the latest progress update."""
        return self._latest_progress


class ProgressRegistry:
    """Global registry of active scrape progress broadcasters.

    Singleton pattern - one registry for the entire application.
    """

    _instance: "ProgressRegistry | None" = None
    _broadcasters: dict[int, ProgressBroadcaster]

    def __new__(cls) -> "ProgressRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._broadcasters = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ProgressRegistry":
        """Get the singleton registry instance."""
        return cls()

    def create_broadcaster(self, scrape_run_id: int) -> ProgressBroadcaster:
        """Create a new broadcaster for a scrape run.

        Args:
            scrape_run_id: ID of the scrape run.

        Returns:
            The created broadcaster.
        """
        broadcaster = ProgressBroadcaster(scrape_run_id)
        self._broadcasters[scrape_run_id] = broadcaster
        return broadcaster

    def get_broadcaster(self, scrape_run_id: int) -> ProgressBroadcaster | None:
        """Get an existing broadcaster by scrape run ID.

        Args:
            scrape_run_id: ID of the scrape run.

        Returns:
            The broadcaster, or None if not found.
        """
        return self._broadcasters.get(scrape_run_id)

    def remove_broadcaster(self, scrape_run_id: int) -> None:
        """Remove a broadcaster from the registry.

        Args:
            scrape_run_id: ID of the scrape run.
        """
        self._broadcasters.pop(scrape_run_id, None)

    def get_active_scrape_ids(self) -> list[int]:
        """Get IDs of all active (non-completed) scrapes.

        Returns:
            List of scrape run IDs with active broadcasters.
        """
        return [
            run_id
            for run_id, broadcaster in self._broadcasters.items()
            if not broadcaster.is_completed
        ]


# Global registry instance
progress_registry = ProgressRegistry.get_instance()
