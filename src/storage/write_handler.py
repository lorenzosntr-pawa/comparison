"""Write handler - performs actual DB operations for a WriteBatch.

Opens its own async session (isolated from scraping) and processes:
- INSERT for changed BetPawa and competitor snapshots (with markets)
- UPDATE last_confirmed_at for unchanged snapshot IDs

Session Isolation:
    The handler receives a session_factory and opens its own session
    for each batch. This isolates write operations from the scraping
    session, preventing transaction interference.

Processing Steps:
    1. INSERT changed OddsSnapshot records (BetPawa)
    2. INSERT changed CompetitorOddsSnapshot records
    3. flush() to get snapshot IDs
    4. INSERT MarketOdds/CompetitorMarketOdds with snapshot_id FK
    5. UPDATE last_confirmed_at for unchanged snapshot IDs
    6. commit()

Error Handling:
    - IntegrityError: Log warning, skip batch (concurrent write conflict)
    - OperationalError: Rollback and re-raise for retry in AsyncWriteQueue

Helper Functions:
    _build_market_odds(): Convert MarketWriteData to MarketOdds ORM
    _build_competitor_market_odds(): Convert to CompetitorMarketOdds ORM
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, OperationalError

from src.db.models.competitor import CompetitorMarketOdds, CompetitorOddsSnapshot
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.storage.write_queue import (
    CompetitorSnapshotWriteData,
    MarketWriteData,
    SnapshotWriteData,
    UnavailableMarketUpdate,
    WriteBatch,
)

logger = structlog.get_logger("write_handler")


# ---------------------------------------------------------------------------
# Helper: build ORM MarketOdds from dataclass
# ---------------------------------------------------------------------------

def _build_market_odds(mwd: MarketWriteData) -> MarketOdds:
    """Create a MarketOdds ORM object from a MarketWriteData dataclass."""
    return MarketOdds(
        betpawa_market_id=mwd.betpawa_market_id,
        betpawa_market_name=mwd.betpawa_market_name,
        line=mwd.line,
        handicap_type=mwd.handicap_type,
        handicap_home=mwd.handicap_home,
        handicap_away=mwd.handicap_away,
        outcomes=mwd.outcomes,
        market_groups=mwd.market_groups,
        unavailable_at=mwd.unavailable_at,
    )


def _build_competitor_market_odds(mwd: MarketWriteData) -> CompetitorMarketOdds:
    """Create a CompetitorMarketOdds ORM object from a MarketWriteData dataclass."""
    return CompetitorMarketOdds(
        betpawa_market_id=mwd.betpawa_market_id,
        betpawa_market_name=mwd.betpawa_market_name,
        line=mwd.line,
        handicap_type=mwd.handicap_type,
        handicap_home=mwd.handicap_home,
        handicap_away=mwd.handicap_away,
        outcomes=mwd.outcomes,
        market_groups=mwd.market_groups,
        unavailable_at=mwd.unavailable_at,
    )


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

async def handle_write_batch(session_factory, batch: WriteBatch) -> dict:
    """Process a WriteBatch: INSERT changed snapshots, UPDATE unchanged timestamps.

    Opens its own DB session (isolated from scraping session).
    Returns stats dict with counts and timing.

    Raises
    ------
    OperationalError
        Re-raised to trigger retry in AsyncWriteQueue._process_with_retry.
    """
    t0 = time.perf_counter()
    inserted_bp = 0
    inserted_comp = 0
    updated_bp = 0
    updated_comp = 0
    unavailable_bp_count = 0
    unavailable_comp_count = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    async with session_factory() as db:
        try:
            # ----------------------------------------------------------
            # 1. INSERT changed BetPawa snapshots
            # ----------------------------------------------------------
            bp_snapshots: list[tuple[OddsSnapshot, tuple[MarketWriteData, ...]]] = []
            for swd in batch.changed_betpawa:
                snapshot = OddsSnapshot(
                    event_id=swd.event_id,
                    bookmaker_id=swd.bookmaker_id,
                    scrape_run_id=swd.scrape_run_id,
                    last_confirmed_at=now,
                )
                db.add(snapshot)
                bp_snapshots.append((snapshot, swd.markets))
                inserted_bp += 1

            # ----------------------------------------------------------
            # 2. INSERT changed competitor snapshots
            # ----------------------------------------------------------
            comp_snapshots: list[tuple[CompetitorOddsSnapshot, tuple[MarketWriteData, ...]]] = []
            for cswd in batch.changed_competitor:
                snapshot = CompetitorOddsSnapshot(
                    competitor_event_id=cswd.competitor_event_id,
                    scrape_run_id=cswd.scrape_run_id,
                    last_confirmed_at=now,
                )
                db.add(snapshot)
                comp_snapshots.append((snapshot, cswd.markets))
                inserted_comp += 1

            # Flush to get snapshot IDs for market rows
            if bp_snapshots or comp_snapshots:
                await db.flush()

            # Add market rows with their snapshot IDs
            for snapshot, market_data in bp_snapshots:
                for mwd in market_data:
                    market = _build_market_odds(mwd)
                    market.snapshot_id = snapshot.id
                    db.add(market)

            for snapshot, market_data in comp_snapshots:
                for mwd in market_data:
                    market = _build_competitor_market_odds(mwd)
                    market.snapshot_id = snapshot.id
                    db.add(market)

            # ----------------------------------------------------------
            # 3. UPDATE unchanged BetPawa timestamps
            # ----------------------------------------------------------
            if batch.unchanged_betpawa_ids:
                await db.execute(
                    update(OddsSnapshot)
                    .where(OddsSnapshot.id.in_(list(batch.unchanged_betpawa_ids)))
                    .values(last_confirmed_at=now)
                )
                updated_bp = len(batch.unchanged_betpawa_ids)

            # ----------------------------------------------------------
            # 4. UPDATE unchanged competitor timestamps
            # ----------------------------------------------------------
            if batch.unchanged_competitor_ids:
                await db.execute(
                    update(CompetitorOddsSnapshot)
                    .where(CompetitorOddsSnapshot.id.in_(list(batch.unchanged_competitor_ids)))
                    .values(last_confirmed_at=now)
                )
                updated_comp = len(batch.unchanged_competitor_ids)

            # ----------------------------------------------------------
            # 5. UPDATE unavailable BetPawa markets
            # ----------------------------------------------------------
            for umu in batch.unavailable_betpawa:
                await db.execute(
                    update(MarketOdds)
                    .where(
                        MarketOdds.snapshot_id == umu.snapshot_id,
                        MarketOdds.betpawa_market_id == umu.betpawa_market_id,
                    )
                    .values(unavailable_at=umu.unavailable_at)
                )
                unavailable_bp_count += 1

            # ----------------------------------------------------------
            # 6. UPDATE unavailable competitor markets
            # ----------------------------------------------------------
            for umu in batch.unavailable_competitor:
                await db.execute(
                    update(CompetitorMarketOdds)
                    .where(
                        CompetitorMarketOdds.snapshot_id == umu.snapshot_id,
                        CompetitorMarketOdds.betpawa_market_id == umu.betpawa_market_id,
                    )
                    .values(unavailable_at=umu.unavailable_at)
                )
                unavailable_comp_count += 1

            # ----------------------------------------------------------
            # 7. Commit
            # ----------------------------------------------------------
            await db.commit()

        except IntegrityError as exc:
            # Duplicate key from concurrent writes — log warning, skip batch.
            await db.rollback()
            logger.warning(
                "write_batch_integrity_error",
                batch_index=batch.batch_index,
                error=str(exc),
            )

        except OperationalError:
            # DB connection issue — rollback and re-raise for retry.
            await db.rollback()
            raise

    elapsed_ms = (time.perf_counter() - t0) * 1000
    stats = {
        "inserted_bp": inserted_bp,
        "inserted_comp": inserted_comp,
        "updated_bp": updated_bp,
        "updated_comp": updated_comp,
        "unavailable_bp": unavailable_bp_count,
        "unavailable_comp": unavailable_comp_count,
        "write_ms": round(elapsed_ms, 1),
    }

    logger.debug(
        "write_batch_complete",
        batch_index=batch.batch_index,
        **stats,
    )

    return stats
