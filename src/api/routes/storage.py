"""Storage monitoring API endpoints.

This module provides endpoints for monitoring database storage:
- GET /storage/sizes: Current table sizes and total database size
- GET /storage/history: Historical storage samples for trend analysis
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.storage import (
    StorageHistoryResponse,
    StorageSampleResponse,
    StorageSizes,
    TableSize,
)
from src.db.engine import get_db

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/sizes", response_model=StorageSizes)
async def get_storage_sizes(
    db: AsyncSession = Depends(get_db),
) -> StorageSizes:
    """Get current storage sizes for all database tables.

    Queries PostgreSQL system tables to get actual disk usage for each
    user table, including size in bytes, human-readable format, and
    approximate row counts.

    Args:
        db: Async database session (injected).

    Returns:
        StorageSizes with per-table sizes and total database size.
    """
    # Query table sizes from pg_stat_user_tables
    table_sizes_query = text("""
        SELECT
            relname as table_name,
            pg_total_relation_size(quote_ident(relname)) as size_bytes,
            pg_size_pretty(pg_total_relation_size(quote_ident(relname))) as size_human,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(quote_ident(relname)) DESC
    """)

    result = await db.execute(table_sizes_query)
    rows = result.fetchall()

    tables = [
        TableSize(
            table_name=row.table_name,
            size_bytes=row.size_bytes,
            size_human=row.size_human,
            row_count=row.row_count,
        )
        for row in rows
    ]

    # Query total database size
    total_size_query = text("""
        SELECT
            pg_database_size(current_database()) as total_bytes,
            pg_size_pretty(pg_database_size(current_database())) as total_human
    """)

    total_result = await db.execute(total_size_query)
    total_row = total_result.fetchone()

    return StorageSizes(
        tables=tables,
        total_bytes=total_row.total_bytes,
        total_human=total_row.total_human,
        measured_at=datetime.now(timezone.utc),
    )


@router.get("/history", response_model=StorageHistoryResponse)
async def get_storage_history(
    limit: int = Query(30, ge=1, le=100, description="Maximum samples to return"),
    db: AsyncSession = Depends(get_db),
) -> StorageHistoryResponse:
    """Get historical storage samples for trend analysis.

    Returns recent storage samples ordered by most recent first.
    Default limit is 30 samples (approximately 1 month of daily samples).

    Args:
        limit: Maximum number of samples to return (1-100, default 30).
        db: Async database session (injected).

    Returns:
        StorageHistoryResponse with list of samples and total count.
    """
    # Deferred import to avoid circular dependency
    from src.db.models.storage_sample import StorageSample

    # Get total count
    count_result = await db.execute(select(func.count(StorageSample.id)))
    total = count_result.scalar_one()

    # Get recent samples
    result = await db.execute(
        select(StorageSample)
        .order_by(desc(StorageSample.sampled_at))
        .limit(limit)
    )
    samples = result.scalars().all()

    return StorageHistoryResponse(
        samples=[StorageSampleResponse.model_validate(sample) for sample in samples],
        total=total,
    )
