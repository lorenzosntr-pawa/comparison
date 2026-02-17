"""Async write queue for background database persistence.

Decouples scraping from DB writes: scraped data is enqueued as plain
frozen dataclasses, and a background worker processes them with automatic
retry and exponential backoff. Scraping never waits for DB commits.

Data Structures (Frozen Dataclasses):
    MarketWriteData: Plain data for creating a MarketOdds row
    SnapshotWriteData: BetPawa snapshot with markets tuple
    CompetitorSnapshotWriteData: Competitor snapshot with markets tuple
    WriteBatch: Complete batch with changed/unchanged separation

Queue Characteristics:
    - Bounded: maxsize parameter provides backpressure
    - Single worker: One background task processes batches sequentially
    - Retry: 3 attempts with exponential backoff (1s, 2s, 4s)

Lifecycle:
    queue = AsyncWriteQueue(session_factory, maxsize=50)
    await queue.start()  # Spawns worker task
    await queue.enqueue(batch)  # Blocks if full
    await queue.stop()  # Drains remaining items, then stops

Benefits:
    - Scraping throughput not blocked by DB latency
    - Failed writes don't crash scrape cycle
    - Backpressure prevents unbounded memory growth
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime

import structlog


# ---------------------------------------------------------------------------
# Data structures (frozen dataclasses — no ORM dependency)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketWriteData:
    """Plain data for creating a MarketOdds row."""

    betpawa_market_id: str
    betpawa_market_name: str
    line: float | None
    handicap_type: str | None
    handicap_home: float | None
    handicap_away: float | None
    outcomes: dict  # [{name, odds, is_active}, ...]
    market_groups: list[str] | None
    unavailable_at: datetime | None = None


@dataclass(frozen=True)
class SnapshotWriteData:
    """Plain data for creating an OddsSnapshot — no ORM dependency."""

    event_id: int
    bookmaker_id: int
    scrape_run_id: int | None
    markets: tuple[MarketWriteData, ...]


@dataclass(frozen=True)
class CompetitorSnapshotWriteData:
    """Plain data for creating a CompetitorOddsSnapshot."""

    competitor_event_id: int
    scrape_run_id: int | None
    markets: tuple[MarketWriteData, ...]


@dataclass(frozen=True)
class UnavailableMarketUpdate:
    """Track a market that became unavailable - needs UPDATE on existing row."""

    snapshot_id: int
    betpawa_market_id: str
    unavailable_at: datetime


@dataclass(frozen=True)
class WriteBatch:
    """A complete batch of writes to process."""

    changed_betpawa: tuple[SnapshotWriteData, ...]
    changed_competitor: tuple[CompetitorSnapshotWriteData, ...]
    unchanged_betpawa_ids: tuple[int, ...]  # snapshot IDs for last_confirmed_at update
    unchanged_competitor_ids: tuple[int, ...]
    scrape_run_id: int | None
    batch_index: int
    unavailable_betpawa: tuple[UnavailableMarketUpdate, ...] = ()
    unavailable_competitor: tuple[UnavailableMarketUpdate, ...] = ()


# ---------------------------------------------------------------------------
# Retry constants
# ---------------------------------------------------------------------------

_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECS = 1.0  # 1s, 2s, 4s


# ---------------------------------------------------------------------------
# AsyncWriteQueue
# ---------------------------------------------------------------------------

class AsyncWriteQueue:
    """Bounded async queue with a single background worker for DB writes.

    Parameters
    ----------
    session_factory:
        An ``async_sessionmaker`` used by the write handler to open its
        own isolated DB session for each batch.
    maxsize:
        Maximum number of ``WriteBatch`` items the queue can hold before
        ``enqueue()`` blocks (backpressure).
    """

    def __init__(self, session_factory, maxsize: int = 50):
        self._queue: asyncio.Queue[WriteBatch] = asyncio.Queue(maxsize=maxsize)
        self._session_factory = session_factory  # async_sessionmaker
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self._log = structlog.get_logger("write_queue")

    # -- lifecycle -----------------------------------------------------------

    async def start(self) -> None:
        """Start the background worker task."""
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        self._log.info("write_queue_started", maxsize=self._queue.maxsize)

    async def stop(self) -> None:
        """Signal stop, drain remaining items, then cancel worker."""
        self._running = False
        if self._worker_task:
            # Process remaining items before stopping
            await self._drain()
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._log.info("write_queue_stopped")

    # -- public API ----------------------------------------------------------

    async def enqueue(self, batch: WriteBatch) -> None:
        """Add a write batch to the queue.

        Blocks if the queue is full (backpressure).
        """
        await self._queue.put(batch)
        self._log.debug(
            "write_batch_enqueued",
            batch_index=batch.batch_index,
            changed_bp=len(batch.changed_betpawa),
            changed_comp=len(batch.changed_competitor),
            unchanged_bp=len(batch.unchanged_betpawa_ids),
            unchanged_comp=len(batch.unchanged_competitor_ids),
            unavailable_bp=len(batch.unavailable_betpawa),
            unavailable_comp=len(batch.unavailable_competitor),
        )

    def stats(self) -> dict:
        """Return queue statistics."""
        return {
            "queue_size": self._queue.qsize(),
            "queue_maxsize": self._queue.maxsize,
            "running": self._running,
        }

    # -- internals -----------------------------------------------------------

    async def _worker_loop(self) -> None:
        """Main worker: dequeue and process batches."""
        while self._running or not self._queue.empty():
            try:
                batch = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            await self._process_with_retry(batch)
            self._queue.task_done()

    async def _drain(self) -> None:
        """Process all remaining items in the queue."""
        while not self._queue.empty():
            batch = self._queue.get_nowait()
            await self._process_with_retry(batch)
            self._queue.task_done()

    async def _process_with_retry(self, batch: WriteBatch) -> None:
        """Process a batch with retry + exponential backoff.

        - Max ``_MAX_ATTEMPTS`` attempts.
        - On final failure: log error with batch details, do NOT re-enqueue.
        - On success: log with write_ms timing.
        """
        from src.storage.write_handler import handle_write_batch

        last_exc: BaseException | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            t0 = time.perf_counter()
            try:
                stats = await handle_write_batch(self._session_factory, batch)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                self._log.info(
                    "write_batch_processed",
                    batch_index=batch.batch_index,
                    attempt=attempt,
                    **stats,
                )
                return
            except Exception as exc:
                last_exc = exc
                elapsed_ms = (time.perf_counter() - t0) * 1000
                if attempt < _MAX_ATTEMPTS:
                    backoff = _BASE_BACKOFF_SECS * (2 ** (attempt - 1))
                    self._log.warning(
                        "write_batch_retry",
                        batch_index=batch.batch_index,
                        attempt=attempt,
                        backoff_s=backoff,
                        error=str(exc),
                        write_ms=round(elapsed_ms, 1),
                    )
                    await asyncio.sleep(backoff)

        # All attempts exhausted — log and drop the batch.
        self._log.error(
            "write_batch_failed",
            batch_index=batch.batch_index,
            attempts=_MAX_ATTEMPTS,
            error=str(last_exc),
            changed_bp=len(batch.changed_betpawa),
            changed_comp=len(batch.changed_competitor),
            unchanged_bp=len(batch.unchanged_betpawa_ids),
            unchanged_comp=len(batch.unchanged_competitor_ids),
        )
