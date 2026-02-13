"""Market mapping CRUD API endpoints.

Provides endpoints for:
- Listing merged mappings (code + DB)
- Getting mapping details
- Creating user-defined mappings
- Updating user mappings
- Soft-deleting (deactivating) user mappings
- Hot reload of mapping cache

The list and detail endpoints serve from the in-memory MappingCache,
which merges code-defined and database mappings at runtime.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.mappings import (
    CreateMappingRequest,
    MappingDetailResponse,
    MappingListItem,
    MappingListResponse,
    OutcomeMappingSchema,
    ReloadResponse,
    UpdateMappingRequest,
)
from src.db.engine import get_db
from src.db.models.mapping import MappingAuditLog, UserMarketMapping
from src.market_mapping.cache import mapping_cache

router = APIRouter(prefix="/mappings", tags=["mappings"])


@router.get("", response_model=MappingListResponse)
async def list_mappings(
    source: str | None = Query(None, description="Filter by source: code, db"),
    search: str | None = Query(None, description="Search in canonical_id and name"),
    platform: str | None = Query(None, description="Filter by platform support"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> MappingListResponse:
    """List all mappings (merged view of code + DB).

    Returns paginated list of all market mappings from the in-memory cache.
    Supports filtering by source, platform, and text search.

    Args:
        source: Filter by 'code' or 'db' source.
        search: Filter by text in canonical_id or name (case-insensitive).
        platform: Filter by platform support ('betpawa', 'sportybet', 'bet9ja').
        page: Page number, 1-indexed.
        page_size: Items per page (1-100).

    Returns:
        MappingListResponse with paginated mapping summaries.
    """
    all_mappings = mapping_cache.get_all()

    # Apply filters
    filtered = all_mappings
    if source:
        filtered = [m for m in filtered if m.source == source]
    if search:
        search_lower = search.lower()
        filtered = [
            m
            for m in filtered
            if search_lower in m.canonical_id.lower() or search_lower in m.name.lower()
        ]
    if platform:
        if platform == "betpawa":
            filtered = [m for m in filtered if m.betpawa_id]
        elif platform == "sportybet":
            filtered = [m for m in filtered if m.sportybet_id]
        elif platform == "bet9ja":
            filtered = [m for m in filtered if m.bet9ja_key]

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    items = [
        MappingListItem(
            canonical_id=m.canonical_id,
            name=m.name,
            betpawa_id=m.betpawa_id,
            sportybet_id=m.sportybet_id,
            bet9ja_key=m.bet9ja_key,
            outcome_count=len(m.outcome_mapping),
            source=m.source,
            is_active=True,  # Cached mappings are always active
            priority=m.priority,
        )
        for m in page_items
    ]

    return MappingListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{canonical_id}", response_model=MappingDetailResponse)
async def get_mapping(canonical_id: str) -> MappingDetailResponse:
    """Get single mapping with full details.

    Returns complete mapping information including all outcome definitions.

    Args:
        canonical_id: Unique market identifier.

    Returns:
        MappingDetailResponse with full mapping details.

    Raises:
        HTTPException 404: If mapping not found in cache.
    """
    mapping = mapping_cache.find_by_canonical_id(canonical_id)
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping not found: {canonical_id}")

    return MappingDetailResponse(
        canonical_id=mapping.canonical_id,
        name=mapping.name,
        betpawa_id=mapping.betpawa_id,
        sportybet_id=mapping.sportybet_id,
        bet9ja_key=mapping.bet9ja_key,
        outcome_mapping=[
            OutcomeMappingSchema(
                canonical_id=o.canonical_id,
                betpawa_name=o.betpawa_name,
                sportybet_desc=o.sportybet_desc,
                bet9ja_suffix=o.bet9ja_suffix,
                position=o.position,
            )
            for o in mapping.outcome_mapping
        ],
        source=mapping.source,
        is_active=True,
        priority=mapping.priority,
        created_at=None,  # Code mappings don't have timestamps
        updated_at=None,
    )


@router.post("", response_model=MappingDetailResponse, status_code=201)
async def create_mapping(
    request: CreateMappingRequest,
    db: AsyncSession = Depends(get_db),
) -> MappingDetailResponse:
    """Create new user mapping.

    Creates a database mapping that will be merged with code mappings
    at runtime. Triggers cache reload after creation.

    Args:
        request: Mapping data to create.
        db: Database session (injected).

    Returns:
        MappingDetailResponse with created mapping details.

    Raises:
        HTTPException 400: If canonical_id already exists in database.
    """
    # Check if canonical_id already exists in DB
    existing = await db.execute(
        select(UserMarketMapping).where(UserMarketMapping.canonical_id == request.canonical_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail=f"Mapping already exists: {request.canonical_id}"
        )

    # Create mapping
    mapping = UserMarketMapping(
        canonical_id=request.canonical_id,
        name=request.name,
        betpawa_id=request.betpawa_id,
        sportybet_id=request.sportybet_id,
        bet9ja_key=request.bet9ja_key,
        outcome_mapping=[o.model_dump() for o in request.outcome_mapping],
        priority=request.priority,
        is_active=True,
    )
    db.add(mapping)

    # Create audit log
    audit = MappingAuditLog(
        canonical_id=request.canonical_id,
        action="CREATE",
        old_value=None,
        new_value=_mapping_to_dict(mapping),
        reason=request.reason,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(mapping)

    # Reload cache
    await mapping_cache.load(db)

    return _mapping_to_response(mapping)


@router.patch("/{canonical_id}", response_model=MappingDetailResponse)
async def update_mapping(
    canonical_id: str,
    request: UpdateMappingRequest,
    db: AsyncSession = Depends(get_db),
) -> MappingDetailResponse:
    """Update existing user mapping (partial update).

    Only updates provided fields. Cannot update code-only mappings
    unless a DB override exists.

    Args:
        canonical_id: Unique market identifier.
        request: Fields to update (only non-null fields applied).
        db: Database session (injected).

    Returns:
        MappingDetailResponse with updated mapping details.

    Raises:
        HTTPException 400: If attempting to update code-only mapping.
        HTTPException 404: If mapping not found in database.
    """
    # Check if code-only mapping (can't update)
    cached = mapping_cache.find_by_canonical_id(canonical_id)
    if cached and cached.source == "code":
        # Check if DB override exists
        result = await db.execute(
            select(UserMarketMapping).where(UserMarketMapping.canonical_id == canonical_id)
        )
        mapping = result.scalar_one_or_none()
        if not mapping:
            raise HTTPException(
                status_code=400,
                detail="Cannot update code-only mapping. Create a DB override instead.",
            )
    else:
        result = await db.execute(
            select(UserMarketMapping).where(UserMarketMapping.canonical_id == canonical_id)
        )
        mapping = result.scalar_one_or_none()
        if not mapping:
            raise HTTPException(status_code=404, detail=f"Mapping not found: {canonical_id}")

    # Store old value for audit
    old_value = _mapping_to_dict(mapping)

    # Apply updates
    update_data = request.model_dump(exclude_unset=True, exclude={"reason"})
    if "outcome_mapping" in update_data and update_data["outcome_mapping"] is not None:
        update_data["outcome_mapping"] = [
            o.model_dump() if hasattr(o, "model_dump") else o
            for o in update_data["outcome_mapping"]
        ]

    for field, value in update_data.items():
        setattr(mapping, field, value)

    # Create audit log
    audit = MappingAuditLog(
        mapping_id=mapping.id,
        canonical_id=canonical_id,
        action="UPDATE",
        old_value=old_value,
        new_value=_mapping_to_dict(mapping),
        reason=request.reason,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(mapping)

    # Reload cache
    await mapping_cache.load(db)

    return _mapping_to_response(mapping)


@router.delete("/{canonical_id}", status_code=204)
async def delete_mapping(
    canonical_id: str,
    reason: str | None = Query(None, description="Reason for deletion"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete (deactivate) user mapping.

    Sets is_active=False rather than physically deleting.
    Cannot delete code-only mappings.

    Args:
        canonical_id: Unique market identifier.
        reason: Optional reason for audit log.
        db: Database session (injected).

    Raises:
        HTTPException 400: If attempting to delete code-only mapping.
        HTTPException 404: If mapping not found in database.
    """
    # Check if code-only mapping
    cached = mapping_cache.find_by_canonical_id(canonical_id)
    if cached and cached.source == "code":
        result = await db.execute(
            select(UserMarketMapping).where(UserMarketMapping.canonical_id == canonical_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Cannot delete code-only mapping")

    result = await db.execute(
        select(UserMarketMapping).where(UserMarketMapping.canonical_id == canonical_id)
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping not found: {canonical_id}")

    # Soft delete
    old_value = _mapping_to_dict(mapping)
    mapping.is_active = False

    # Create audit log
    audit = MappingAuditLog(
        mapping_id=mapping.id,
        canonical_id=canonical_id,
        action="DEACTIVATE",
        old_value=old_value,
        new_value=_mapping_to_dict(mapping),
        reason=reason,
    )
    db.add(audit)

    await db.commit()

    # Reload cache
    await mapping_cache.load(db)


@router.post("/reload", response_model=ReloadResponse)
async def reload_mappings(db: AsyncSession = Depends(get_db)) -> ReloadResponse:
    """Hot reload mapping cache from code + DB.

    Forces cache reload, merging code-defined and database mappings.
    Useful after direct database edits or code deployment.

    Args:
        db: Database session (injected).

    Returns:
        ReloadResponse with reload statistics.
    """
    count = await mapping_cache.load(db)
    return ReloadResponse(
        status="ok",
        mapping_count=count,
        reloaded_at=mapping_cache.loaded_at or datetime.utcnow(),
    )


def _mapping_to_dict(mapping: UserMarketMapping) -> dict:
    """Convert mapping to dict for audit log.

    Args:
        mapping: UserMarketMapping ORM model.

    Returns:
        Dictionary representation for JSON storage.
    """
    return {
        "canonical_id": mapping.canonical_id,
        "name": mapping.name,
        "betpawa_id": mapping.betpawa_id,
        "sportybet_id": mapping.sportybet_id,
        "bet9ja_key": mapping.bet9ja_key,
        "outcome_mapping": mapping.outcome_mapping,
        "priority": mapping.priority,
        "is_active": mapping.is_active,
    }


def _mapping_to_response(mapping: UserMarketMapping) -> MappingDetailResponse:
    """Convert DB mapping to response.

    Args:
        mapping: UserMarketMapping ORM model.

    Returns:
        MappingDetailResponse for API response.
    """
    return MappingDetailResponse(
        canonical_id=mapping.canonical_id,
        name=mapping.name,
        betpawa_id=mapping.betpawa_id,
        sportybet_id=mapping.sportybet_id,
        bet9ja_key=mapping.bet9ja_key,
        outcome_mapping=[
            OutcomeMappingSchema(**o) if isinstance(o, dict) else o
            for o in (mapping.outcome_mapping or [])
        ],
        source="db",
        is_active=mapping.is_active,
        priority=mapping.priority,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )
