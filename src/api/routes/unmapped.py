"""Unmapped market discovery API endpoints.

Provides endpoints for:
- Listing unmapped markets with filtering and pagination
- Getting unmapped market details
- Updating unmapped market status and notes

These endpoints expose the unmapped_market_log table populated
by the UnmappedLogger service during scraping.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.unmapped import (
    UnmappedMarketDetailResponse,
    UnmappedMarketListItem,
    UnmappedMarketListResponse,
    UpdateUnmappedRequest,
)
from src.db.engine import get_db
from src.db.models.mapping import UnmappedMarketLog

router = APIRouter(prefix="/unmapped", tags=["unmapped"])


@router.get("", response_model=UnmappedMarketListResponse)
async def list_unmapped_markets(
    source: str | None = Query(None, description="Filter by platform: sportybet, bet9ja"),
    status: str | None = Query(None, description="Filter by status: NEW, ACKNOWLEDGED, MAPPED, IGNORED"),
    min_occurrences: int | None = Query(None, ge=1, description="Minimum occurrence count"),
    sort_by: str = Query("occurrence_count", description="Sort field: occurrence_count, last_seen_at, first_seen_at"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> UnmappedMarketListResponse:
    """List unmapped markets discovered during scraping.

    Returns paginated list of unmapped markets with filtering support.
    Useful for identifying mapping gaps and prioritizing new mappings.

    Args:
        source: Filter by platform ('sportybet' or 'bet9ja').
        status: Filter by status ('NEW', 'ACKNOWLEDGED', 'MAPPED', 'IGNORED').
        min_occurrences: Only include markets seen at least this many times.
        sort_by: Field to sort by (occurrence_count, last_seen_at, first_seen_at).
        sort_order: Sort direction ('asc' or 'desc').
        page: Page number, 1-indexed.
        page_size: Items per page (1-100).
        db: Database session (injected).

    Returns:
        UnmappedMarketListResponse with paginated unmapped market summaries.
    """
    # Build query
    query = select(UnmappedMarketLog)

    # Apply filters
    if source:
        query = query.where(UnmappedMarketLog.source == source)
    if status:
        query = query.where(UnmappedMarketLog.status == status)
    if min_occurrences:
        query = query.where(UnmappedMarketLog.occurrence_count >= min_occurrences)

    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    sort_column = {
        "occurrence_count": UnmappedMarketLog.occurrence_count,
        "last_seen_at": UnmappedMarketLog.last_seen_at,
        "first_seen_at": UnmappedMarketLog.first_seen_at,
    }.get(sort_by, UnmappedMarketLog.occurrence_count)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    records = result.scalars().all()

    # Convert to response items
    items = [
        UnmappedMarketListItem(
            id=record.id,
            source=record.source,
            external_market_id=record.external_market_id,
            market_name=record.market_name,
            first_seen_at=record.first_seen_at,
            last_seen_at=record.last_seen_at,
            occurrence_count=record.occurrence_count,
            status=record.status,
        )
        for record in records
    ]

    return UnmappedMarketListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{unmapped_id}", response_model=UnmappedMarketDetailResponse)
async def get_unmapped_market(
    unmapped_id: int,
    db: AsyncSession = Depends(get_db),
) -> UnmappedMarketDetailResponse:
    """Get single unmapped market with full details.

    Returns complete unmapped market information including sample outcomes.

    Args:
        unmapped_id: Database ID of the unmapped market.
        db: Database session (injected).

    Returns:
        UnmappedMarketDetailResponse with full market details.

    Raises:
        HTTPException 404: If unmapped market not found.
    """
    result = await db.execute(
        select(UnmappedMarketLog).where(UnmappedMarketLog.id == unmapped_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail=f"Unmapped market not found: {unmapped_id}")

    return UnmappedMarketDetailResponse(
        id=record.id,
        source=record.source,
        external_market_id=record.external_market_id,
        market_name=record.market_name,
        sample_outcomes=record.sample_outcomes,
        first_seen_at=record.first_seen_at,
        last_seen_at=record.last_seen_at,
        occurrence_count=record.occurrence_count,
        status=record.status,
        notes=record.notes,
    )


@router.patch("/{unmapped_id}", response_model=UnmappedMarketDetailResponse)
async def update_unmapped_market(
    unmapped_id: int,
    request: UpdateUnmappedRequest,
    db: AsyncSession = Depends(get_db),
) -> UnmappedMarketDetailResponse:
    """Update unmapped market status or notes.

    Partial update - only provided fields are modified.
    Use this to mark markets as ACKNOWLEDGED, MAPPED, or IGNORED.

    Args:
        unmapped_id: Database ID of the unmapped market.
        request: Fields to update (only non-null fields applied).
        db: Database session (injected).

    Returns:
        UnmappedMarketDetailResponse with updated market details.

    Raises:
        HTTPException 404: If unmapped market not found.
    """
    result = await db.execute(
        select(UnmappedMarketLog).where(UnmappedMarketLog.id == unmapped_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail=f"Unmapped market not found: {unmapped_id}")

    # Apply updates
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    await db.commit()
    await db.refresh(record)

    return UnmappedMarketDetailResponse(
        id=record.id,
        source=record.source,
        external_market_id=record.external_market_id,
        market_name=record.market_name,
        sample_outcomes=record.sample_outcomes,
        first_seen_at=record.first_seen_at,
        last_seen_at=record.last_seen_at,
        occurrence_count=record.occurrence_count,
        status=record.status,
        notes=record.notes,
    )
