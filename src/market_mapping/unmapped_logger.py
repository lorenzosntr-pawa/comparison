"""UnmappedLogger for discovering unmapped markets during scraping.

Captures market information when MappingError occurs during scraping, persists to
database for analysis, and tracks new discoveries for potential WebSocket alerts.

Data Structures:
    UnmappedEntry: Frozen dataclass for in-memory pending entries.

Internal Layout:
    _pending: Dict keyed by (source, external_market_id) for deduplication.
    _new_markets: List of newly discovered markets (not previously in DB).
    _lock: asyncio.Lock for thread-safe access during concurrent scraping.

Cache Pattern:
    Follows established frozen dataclass pattern from MappingCache (v2.0).
    Module-level singleton for app-wide access.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.mapping import UnmappedMarketLog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class UnmappedEntry:
    """Frozen entry for an unmapped market discovered during scraping.

    Attributes:
        source: Platform identifier ("sportybet" or "bet9ja").
        external_market_id: Platform's market ID.
        market_name: Market name from platform (if available).
        sample_outcomes: Example outcomes for reference (first 3).
        seen_at: When this entry was created.
    """

    source: str
    external_market_id: str
    market_name: Optional[str]
    sample_outcomes: Optional[list[dict]]
    seen_at: datetime


class UnmappedLogger:
    """Thread-safe logger for unmapped market discovery.

    Collects unmapped markets during scraping, deduplicates by (source, market_id),
    and persists to database via upsert. Tracks newly discovered markets separately
    for potential real-time alerts.

    Example:
        >>> from market_mapping.unmapped_logger import unmapped_logger, UnmappedEntry
        >>> unmapped_logger.log(UnmappedEntry(
        ...     source="sportybet",
        ...     external_market_id="999",
        ...     market_name="Exotic Market",
        ...     sample_outcomes=[{"desc": "Yes", "odds": "1.50"}],
        ...     seen_at=datetime.now(timezone.utc),
        ... ))
        >>> async with get_session() as session:
        ...     new_count = await unmapped_logger.flush(session)
    """

    def __init__(self) -> None:
        """Initialize empty logger with lock for thread safety."""
        self._pending: dict[tuple[str, str], UnmappedEntry] = {}
        self._new_markets: list[UnmappedEntry] = []
        self._lock = asyncio.Lock()

    def log(self, entry: UnmappedEntry) -> bool:
        """Add unmapped market entry to pending queue.

        Deduplicates by (source, external_market_id) - only keeps the most recent
        entry for each unique market within a scrape cycle.

        Args:
            entry: UnmappedEntry with market information.

        Returns:
            True if this is a new entry (not seen before in this session).
        """
        key = (entry.source, entry.external_market_id)
        is_new = key not in self._pending
        self._pending[key] = entry
        return is_new

    async def flush(self, session: AsyncSession) -> int:
        """Persist all pending entries to database via upsert.

        For each pending entry:
        - If exists in DB: UPDATE last_seen_at and increment occurrence_count
        - If not exists: INSERT new row and add to _new_markets list

        Args:
            session: SQLAlchemy async session for DB operations.

        Returns:
            Count of newly inserted markets (not updates).
        """
        async with self._lock:
            if not self._pending:
                return 0

            new_count = 0
            entries_to_process = list(self._pending.values())
            self._pending.clear()

            for entry in entries_to_process:
                try:
                    # Check if exists in DB
                    result = await session.execute(
                        select(UnmappedMarketLog).where(
                            UnmappedMarketLog.source == entry.source,
                            UnmappedMarketLog.external_market_id == entry.external_market_id,
                        )
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        # Update existing record
                        existing.last_seen_at = datetime.now(timezone.utc)
                        existing.occurrence_count += 1
                        # Update market_name if it was previously null
                        if entry.market_name and not existing.market_name:
                            existing.market_name = entry.market_name
                        # Update sample_outcomes if previously null
                        if entry.sample_outcomes and not existing.sample_outcomes:
                            existing.sample_outcomes = entry.sample_outcomes
                    else:
                        # Insert new record
                        new_record = UnmappedMarketLog(
                            source=entry.source,
                            external_market_id=entry.external_market_id,
                            market_name=entry.market_name,
                            sample_outcomes=entry.sample_outcomes,
                            first_seen_at=entry.seen_at,
                            last_seen_at=entry.seen_at,
                            occurrence_count=1,
                            status="NEW",
                        )
                        session.add(new_record)
                        self._new_markets.append(entry)
                        new_count += 1

                except Exception as e:
                    logger.warning(
                        "unmapped_logger.flush_error",
                        source=entry.source,
                        market_id=entry.external_market_id,
                        error=str(e),
                    )
                    continue

            # Commit all changes
            await session.commit()

            if new_count > 0:
                logger.info(
                    "unmapped_logger.flush_complete",
                    total_processed=len(entries_to_process),
                    new_markets=new_count,
                    updated_markets=len(entries_to_process) - new_count,
                )

            return new_count

    def get_new_markets(self) -> list[UnmappedEntry]:
        """Get list of newly discovered markets from last flush.

        Returns:
            List of UnmappedEntry objects for markets not previously in DB.
        """
        return self._new_markets.copy()

    def clear_new_markets(self) -> None:
        """Clear the new markets list after alerts have been sent."""
        self._new_markets.clear()

    @property
    def pending_count(self) -> int:
        """Number of entries waiting to be flushed."""
        return len(self._pending)


# -----------------------------------------------------------------------------
# Module-level singleton
# -----------------------------------------------------------------------------

unmapped_logger = UnmappedLogger()
"""Global singleton instance for app-wide access."""
