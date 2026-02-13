"""Unmapped market discovery API endpoints.

Provides endpoints for:
- Listing unmapped markets with filtering and pagination
- Getting unmapped market details
- Updating unmapped market status and notes
- Getting high-priority unmapped markets for dashboard

These endpoints expose the unmapped_market_log table populated
by the UnmappedLogger service during scraping.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.unmapped import (
    HighPriorityUnmappedResponse,
    UnmappedMarketDetailResponse,
    UnmappedMarketListItem,
    UnmappedMarketListResponse,
    UpdateUnmappedRequest,
)
from src.db.engine import get_db
from src.db.models.mapping import UnmappedMarketLog

router = APIRouter(prefix="/unmapped", tags=["unmapped"])


def calculate_priority_score(occurrence_count: int, last_seen_at: datetime) -> int:
    """Calculate priority score for unmapped market prioritization.

    Priority score: higher = more important to map.

    Formula:
    - Base: occurrence_count (0-100 points, capped)
    - Recency bonus: +50 if seen in last 24h, +25 if in last 7 days
    - Total: 0-150 range

    Args:
        occurrence_count: Number of times this market has been seen.
        last_seen_at: When the market was last encountered.

    Returns:
        Priority score in range 0-150.
    """
    base = min(occurrence_count, 100)
    now = datetime.utcnow()
    hours_ago = (now - last_seen_at).total_seconds() / 3600
    if hours_ago < 24:
        recency = 50
    elif hours_ago < 168:  # 7 days
        recency = 25
    else:
        recency = 0
    return base + recency


@router.get("", response_model=UnmappedMarketListResponse)
async def list_unmapped_markets(
    source: str | None = Query(None, description="Filter by platform: sportybet, bet9ja"),
    status: str | None = Query(None, description="Filter by status: NEW, ACKNOWLEDGED, MAPPED, IGNORED"),
    min_occurrences: int | None = Query(None, ge=1, description="Minimum occurrence count"),
    sort_by: str = Query("occurrence_count", description="Sort field: occurrence_count, last_seen_at, first_seen_at, priority"),
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
        sort_by: Field to sort by (occurrence_count, last_seen_at, first_seen_at, priority).
        sort_order: Sort direction ('asc' or 'desc').
        page: Page number, 1-indexed.
        page_size: Items per page (1-100).
        db: Database session (injected).

    Returns:
        UnmappedMarketListResponse with paginated unmapped market summaries including priority_score.
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

    # Apply sorting (priority sorting handled post-query)
    sort_column = {
        "occurrence_count": UnmappedMarketLog.occurrence_count,
        "last_seen_at": UnmappedMarketLog.last_seen_at,
        "first_seen_at": UnmappedMarketLog.first_seen_at,
    }.get(sort_by if sort_by != "priority" else None)

    # Priority sorting requires post-fetch sorting
    if sort_by == "priority":
        # Fetch all matching records, sort by priority in Python
        result = await db.execute(query)
        all_records = list(result.scalars().all())

        # Sort by priority score
        all_records.sort(
            key=lambda r: calculate_priority_score(r.occurrence_count, r.last_seen_at),
            reverse=(sort_order != "asc"),
        )

        # Apply pagination after sorting
        offset = (page - 1) * page_size
        records = all_records[offset : offset + page_size]
    else:
        # Standard DB sorting
        if sort_column is not None:
            if sort_order == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            # Default sort by occurrence_count desc
            query = query.order_by(UnmappedMarketLog.occurrence_count.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        records = result.scalars().all()

    # Convert to response items with priority score
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
            priority_score=calculate_priority_score(record.occurrence_count, record.last_seen_at),
        )
        for record in records
    ]

    return UnmappedMarketListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/high-priority", response_model=HighPriorityUnmappedResponse)
async def get_high_priority_unmapped(
    db: AsyncSession = Depends(get_db),
) -> HighPriorityUnmappedResponse:
    """Get top priority unmapped markets for dashboard.

    Returns top 5 NEW status unmapped markets by priority score.
    Useful for the dashboard high-priority section.

    Args:
        db: Database session (injected).

    Returns:
        HighPriorityUnmappedResponse with top 5 high-priority items.
    """
    # Query NEW status unmapped markets only
    query = select(UnmappedMarketLog).where(UnmappedMarketLog.status == "NEW")

    result = await db.execute(query)
    all_records = list(result.scalars().all())

    # Calculate priority and sort
    items_with_priority = [
        (record, calculate_priority_score(record.occurrence_count, record.last_seen_at))
        for record in all_records
    ]
    items_with_priority.sort(key=lambda x: x[1], reverse=True)

    # Take top 5
    top_records = items_with_priority[:5]

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
            priority_score=priority,
        )
        for record, priority in top_records
    ]

    return HighPriorityUnmappedResponse(items=items)


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
