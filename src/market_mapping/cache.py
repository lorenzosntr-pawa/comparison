"""MappingCache for runtime merge of code and DB mappings.

Provides fast in-memory lookup of market mappings with support for user-defined
overrides from the database. Implements the merge strategy where DB mappings
take priority over code-defined mappings on the same canonical_id.

Data Structures:
    OutcomeMapping: Frozen dataclass for cached outcome within a market.
    CachedMapping: Frozen dataclass mirroring MarketMapping with source tracking.

Internal Layout:
    _mappings: Dict[canonical_id, CachedMapping] - primary storage
    _by_betpawa: Dict[betpawa_id, CachedMapping] - index for BetPawa lookup
    _by_sportybet: Dict[sportybet_id, CachedMapping] - index for SportyBet lookup
    _by_bet9ja: Dict[bet9ja_key, CachedMapping] - index for Bet9ja prefix matching

Thread Safety:
    Uses asyncio.Lock for reload operations. Dict reads are safe under GIL.

Cache Pattern:
    Follows established frozen dataclass pattern from OddsCache (v2.0).
    Warmed during app lifespan, available via app.state.mapping_cache.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from market_mapping.mappings import MARKET_MAPPINGS
from market_mapping.types.normalized import MarketMapping

if TYPE_CHECKING:
    from db.models.mapping import UserMarketMapping

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CachedOutcome:
    """Frozen outcome mapping within a market.

    Attributes:
        canonical_id: Canonical outcome identifier (e.g., 'home', 'draw').
        betpawa_name: BetPawa outcome name (e.g., '1', 'X').
        sportybet_desc: SportyBet outcome description.
        bet9ja_suffix: Bet9ja outcome suffix.
        position: Display order position.
    """

    canonical_id: str
    betpawa_name: Optional[str]
    sportybet_desc: Optional[str]
    bet9ja_suffix: Optional[str]
    position: int


@dataclass(frozen=True)
class CachedMapping:
    """Immutable cached mapping for thread-safe access.

    Attributes:
        canonical_id: Unique market identifier (e.g., '1x2_ft').
        name: Human-readable market name.
        betpawa_id: BetPawa marketType.id, None if unmapped.
        sportybet_id: SportyBet market.id, None if unmapped.
        bet9ja_key: Bet9ja key prefix, None if unmapped.
        outcome_mapping: Frozen tuple of outcome mappings.
        source: Origin of mapping - 'code' or 'db'.
        priority: Override priority (higher wins).
    """

    canonical_id: str
    name: str
    betpawa_id: Optional[str]
    sportybet_id: Optional[str]
    bet9ja_key: Optional[str]
    outcome_mapping: tuple[CachedOutcome, ...]
    source: str  # "code" or "db"
    priority: int


class MappingCache:
    """Thread-safe in-memory mapping cache with hot reload.

    Stores merged code and database mappings for fast lookups. Provides
    multiple indexes for efficient access by different platform IDs.

    Merge Strategy:
        1. Load all code MARKET_MAPPINGS as base
        2. Load active DB user_market_mappings
        3. DB mappings override code on same canonical_id

    Example:
        >>> cache = MappingCache()
        >>> async with get_session() as session:
        ...     count = await cache.load(session)
        >>> mapping = cache.find_by_betpawa_id("3743")
        >>> mapping.name
        '1X2 - Full Time'
    """

    def __init__(self) -> None:
        """Initialize empty cache with lock for reload safety."""
        self._mappings: dict[str, CachedMapping] = {}
        self._by_betpawa: dict[str, CachedMapping] = {}
        self._by_sportybet: dict[str, CachedMapping] = {}
        self._by_bet9ja: dict[str, CachedMapping] = {}
        self._lock = asyncio.Lock()
        self._loaded_at: Optional[datetime] = None
        self._count: int = 0
        self._code_count: int = 0
        self._db_count: int = 0

    async def load(self, session: AsyncSession) -> int:
        """Load and merge mappings from code and DB.

        Merges code-defined MARKET_MAPPINGS with active database mappings.
        DB mappings override code mappings on matching canonical_id.

        Args:
            session: SQLAlchemy async session for DB queries.

        Returns:
            Total number of mappings loaded.
        """
        async with self._lock:
            # 1. Start with code mappings
            merged: dict[str, CachedMapping] = {}
            for mapping in MARKET_MAPPINGS:
                cached = self._from_code(mapping)
                merged[cached.canonical_id] = cached
            self._code_count = len(merged)

            # 2. Load DB mappings (active only)
            from src.db.models.mapping import UserMarketMapping

            result = await session.execute(
                select(UserMarketMapping).where(UserMarketMapping.is_active == True)
            )
            db_mappings = result.scalars().all()

            # 3. Merge: DB overrides code on same canonical_id
            db_override_count = 0
            db_new_count = 0
            for db_map in db_mappings:
                if db_map.canonical_id in merged:
                    db_override_count += 1
                else:
                    db_new_count += 1
                cached = self._from_db(db_map)
                merged[cached.canonical_id] = cached
            self._db_count = len(db_mappings)

            # 4. Build indexes
            self._mappings = merged
            self._by_betpawa = {
                m.betpawa_id: m for m in merged.values() if m.betpawa_id
            }
            self._by_sportybet = {
                m.sportybet_id: m for m in merged.values() if m.sportybet_id
            }
            self._by_bet9ja = {
                m.bet9ja_key: m for m in merged.values() if m.bet9ja_key
            }
            self._loaded_at = datetime.utcnow()
            self._count = len(merged)

            logger.info(
                "mapping_cache.loaded",
                total=self._count,
                code=self._code_count,
                db=self._db_count,
                db_overrides=db_override_count,
                db_new=db_new_count,
            )

            return self._count

    async def reload(self, session: AsyncSession) -> int:
        """Reload mappings from code and DB (hot reload).

        Clears existing cache and reloads all mappings. Thread-safe
        via asyncio.Lock - readers will see consistent state.

        Args:
            session: SQLAlchemy async session for DB queries.

        Returns:
            Total number of mappings after reload.
        """
        logger.info("mapping_cache.reload_start")
        count = await self.load(session)
        logger.info("mapping_cache.reload_done", total=count)
        return count

    def _from_code(self, mapping: MarketMapping) -> CachedMapping:
        """Convert code MarketMapping to CachedMapping.

        Args:
            mapping: Pydantic MarketMapping from MARKET_MAPPINGS.

        Returns:
            Frozen CachedMapping for cache storage.
        """
        outcomes = tuple(
            CachedOutcome(
                canonical_id=o.canonical_id,
                betpawa_name=o.betpawa_name,
                sportybet_desc=o.sportybet_desc,
                bet9ja_suffix=o.bet9ja_suffix,
                position=o.position,
            )
            for o in mapping.outcome_mapping
        )
        return CachedMapping(
            canonical_id=mapping.canonical_id,
            name=mapping.name,
            betpawa_id=mapping.betpawa_id,
            sportybet_id=mapping.sportybet_id,
            bet9ja_key=mapping.bet9ja_key,
            outcome_mapping=outcomes,
            source="code",
            priority=0,
        )

    def _from_db(self, mapping: UserMarketMapping) -> CachedMapping:
        """Convert DB UserMarketMapping to CachedMapping.

        Args:
            mapping: SQLAlchemy UserMarketMapping model.

        Returns:
            Frozen CachedMapping for cache storage.
        """
        outcomes = tuple(
            CachedOutcome(
                canonical_id=o.get("canonical_id", ""),
                betpawa_name=o.get("betpawa_name"),
                sportybet_desc=o.get("sportybet_desc"),
                bet9ja_suffix=o.get("bet9ja_suffix"),
                position=o.get("position", 0),
            )
            for o in (mapping.outcome_mapping or [])
        )
        return CachedMapping(
            canonical_id=mapping.canonical_id,
            name=mapping.name,
            betpawa_id=mapping.betpawa_id,
            sportybet_id=mapping.sportybet_id,
            bet9ja_key=mapping.bet9ja_key,
            outcome_mapping=outcomes,
            source="db",
            priority=mapping.priority,
        )

    # -------------------------------------------------------------------------
    # Lookup methods (read)
    # -------------------------------------------------------------------------

    def find_by_canonical_id(self, id: str) -> Optional[CachedMapping]:
        """Find mapping by canonical_id.

        Args:
            id: Canonical market identifier (e.g., '1x2_ft').

        Returns:
            CachedMapping if found, None otherwise.
        """
        return self._mappings.get(id)

    def find_by_betpawa_id(self, id: str) -> Optional[CachedMapping]:
        """Find mapping by BetPawa market ID.

        Args:
            id: BetPawa marketType.id (e.g., '3743').

        Returns:
            CachedMapping if found, None otherwise.
        """
        return self._by_betpawa.get(id)

    def find_by_sportybet_id(self, id: str) -> Optional[CachedMapping]:
        """Find mapping by SportyBet market ID.

        Args:
            id: SportyBet market.id (e.g., '1').

        Returns:
            CachedMapping if found, None otherwise.
        """
        return self._by_sportybet.get(id)

    def find_by_bet9ja_key(self, key: str) -> Optional[CachedMapping]:
        """Find mapping by Bet9ja key using prefix matching.

        Bet9ja uses prefix-based keys (e.g., 'S_1X2_1' matches 'S_1X2').
        Iterates through all bet9ja keys and returns first prefix match.

        Args:
            key: Full Bet9ja market key (e.g., 'S_1X2_1').

        Returns:
            CachedMapping if prefix match found, None otherwise.
        """
        for prefix, mapping in self._by_bet9ja.items():
            if key.startswith(prefix):
                return mapping
        return None

    def get_all(self) -> list[CachedMapping]:
        """Get all cached mappings.

        Returns:
            List of all CachedMapping entries.
        """
        return list(self._mappings.values())

    def get_by_source(self, source: str) -> list[CachedMapping]:
        """Get mappings filtered by source.

        Args:
            source: 'code' or 'db'.

        Returns:
            List of CachedMapping entries from specified source.
        """
        return [m for m in self._mappings.values() if m.source == source]

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def loaded_at(self) -> Optional[datetime]:
        """When cache was last loaded."""
        return self._loaded_at

    @property
    def count(self) -> int:
        """Total number of mappings in cache."""
        return self._count

    @property
    def code_count(self) -> int:
        """Number of code-defined mappings (before DB override)."""
        return self._code_count

    @property
    def db_count(self) -> int:
        """Number of DB-defined mappings loaded."""
        return self._db_count

    def stats(self) -> dict:
        """Return cache statistics.

        Returns:
            Dict with count, source breakdown, and load timestamp.
        """
        return {
            "total": self._count,
            "code": self._code_count,
            "db": self._db_count,
            "by_betpawa": len(self._by_betpawa),
            "by_sportybet": len(self._by_sportybet),
            "by_bet9ja": len(self._by_bet9ja),
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
        }


# -----------------------------------------------------------------------------
# Module-level singleton
# -----------------------------------------------------------------------------

_mapping_cache: MappingCache | None = None
"""Private singleton instance. Use get_mapping_cache() to access."""


def get_mapping_cache() -> MappingCache:
    """Get global mapping cache singleton.

    Returns:
        The initialized MappingCache instance.

    Raises:
        RuntimeError: If cache has not been initialized via init_mapping_cache().
    """
    if _mapping_cache is None:
        raise RuntimeError(
            "MappingCache not initialized. Call init_mapping_cache() first."
        )
    return _mapping_cache


def is_mapping_cache_initialized() -> bool:
    """Check if the mapping cache has been initialized.

    Returns:
        True if init_mapping_cache() has been called, False otherwise.
    """
    return _mapping_cache is not None


async def init_mapping_cache(session: AsyncSession) -> MappingCache:
    """Initialize global mapping cache singleton.

    Loads and merges code + DB mappings into the global cache.
    Should be called once during app startup after DB is ready.

    Args:
        session: SQLAlchemy async session for DB queries.

    Returns:
        The initialized MappingCache instance.
    """
    global _mapping_cache
    _mapping_cache = MappingCache()
    await _mapping_cache.load(session)
    logger.info(
        "mapping_cache.singleton_initialized",
        total=_mapping_cache.count,
        code=_mapping_cache.code_count,
        db=_mapping_cache.db_count,
    )
    return _mapping_cache


# Legacy alias for backward compatibility
mapping_cache = MappingCache()
"""Global singleton instance for app-wide access.

DEPRECATED: Use get_mapping_cache() instead. This instance may not be loaded.
"""
