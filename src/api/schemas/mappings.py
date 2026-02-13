"""Pydantic schemas for mappings API endpoints.

This module defines schemas for the market mapping management API:
- OutcomeMappingSchema: Single outcome mapping within a market
- MappingListItem: Summary item for paginated listing
- MappingListResponse: Paginated list response
- MappingDetailResponse: Full mapping details
- CreateMappingRequest: Create new user mapping
- UpdateMappingRequest: Partial update for existing mapping
- ReloadResponse: Cache reload confirmation

Uses camelCase aliases for frontend compatibility.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class OutcomeMappingSchema(BaseModel):
    """Single outcome mapping within a market.

    Attributes:
        canonical_id: Canonical outcome identifier (e.g., 'home', 'draw').
        betpawa_name: BetPawa outcome name (e.g., '1', 'X').
        sportybet_desc: SportyBet outcome description.
        bet9ja_suffix: Bet9ja outcome suffix.
        position: Display order position.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    canonical_id: str = Field(description="Canonical outcome identifier")
    betpawa_name: str | None = Field(default=None, description="BetPawa outcome name")
    sportybet_desc: str | None = Field(default=None, description="SportyBet description")
    bet9ja_suffix: str | None = Field(default=None, description="Bet9ja suffix")
    position: int = Field(description="Display order position")


class MappingListItem(BaseModel):
    """Summary item for mapping list.

    Contains essential fields for list display without full outcome details.

    Attributes:
        canonical_id: Unique market identifier.
        name: Human-readable market name.
        betpawa_id: BetPawa marketType.id, null if unmapped.
        sportybet_id: SportyBet market.id, null if unmapped.
        bet9ja_key: Bet9ja key prefix, null if unmapped.
        outcome_count: Number of outcomes in mapping.
        source: Origin of mapping - 'code' or 'db'.
        is_active: Whether mapping is active.
        priority: Override priority (higher wins).
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    canonical_id: str = Field(description="Unique market identifier")
    name: str = Field(description="Human-readable market name")
    betpawa_id: str | None = Field(default=None, description="BetPawa marketType.id")
    sportybet_id: str | None = Field(default=None, description="SportyBet market.id")
    bet9ja_key: str | None = Field(default=None, description="Bet9ja key prefix")
    outcome_count: int = Field(description="Number of outcomes")
    source: str = Field(description="Origin: 'code' or 'db'")
    is_active: bool = Field(default=True, description="Whether mapping is active")
    priority: int = Field(default=0, description="Override priority")


class MappingListResponse(BaseModel):
    """Paginated list of mappings.

    Standard pagination response with items and metadata.

    Attributes:
        items: List of mapping summaries.
        total: Total count before pagination.
        page: Current page number (1-indexed).
        page_size: Items per page.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    items: list[MappingListItem] = Field(description="Mapping summaries")
    total: int = Field(description="Total count before pagination")
    page: int = Field(description="Current page (1-indexed)")
    page_size: int = Field(description="Items per page")


class MappingDetailResponse(BaseModel):
    """Full mapping details.

    Complete mapping information including outcome definitions.

    Attributes:
        canonical_id: Unique market identifier.
        name: Human-readable market name.
        betpawa_id: BetPawa marketType.id, null if unmapped.
        sportybet_id: SportyBet market.id, null if unmapped.
        bet9ja_key: Bet9ja key prefix, null if unmapped.
        outcome_mapping: Full outcome mapping definitions.
        source: Origin of mapping - 'code' or 'db'.
        is_active: Whether mapping is active.
        priority: Override priority (higher wins).
        created_at: Creation timestamp (DB mappings only).
        updated_at: Last modification timestamp (DB mappings only).
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    canonical_id: str = Field(description="Unique market identifier")
    name: str = Field(description="Human-readable market name")
    betpawa_id: str | None = Field(default=None, description="BetPawa marketType.id")
    sportybet_id: str | None = Field(default=None, description="SportyBet market.id")
    bet9ja_key: str | None = Field(default=None, description="Bet9ja key prefix")
    outcome_mapping: list[OutcomeMappingSchema] = Field(description="Outcome definitions")
    source: str = Field(description="Origin: 'code' or 'db'")
    is_active: bool = Field(default=True, description="Whether mapping is active")
    priority: int = Field(default=0, description="Override priority")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last modification")


class CreateMappingRequest(BaseModel):
    """Create new user mapping.

    Request body for POST /api/mappings. All platform IDs are optional
    but at least one should be provided for a useful mapping.

    Attributes:
        canonical_id: Unique market identifier (1-100 chars).
        name: Human-readable market name (1-255 chars).
        betpawa_id: BetPawa marketType.id (max 50 chars).
        sportybet_id: SportyBet market.id (max 50 chars).
        bet9ja_key: Bet9ja key prefix (max 50 chars).
        outcome_mapping: Outcome definitions (required).
        priority: Override priority 0-100.
        reason: Optional reason for audit log.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    canonical_id: str = Field(min_length=1, max_length=100, description="Unique identifier")
    name: str = Field(min_length=1, max_length=255, description="Market name")
    betpawa_id: str | None = Field(default=None, max_length=50, description="BetPawa ID")
    sportybet_id: str | None = Field(default=None, max_length=50, description="SportyBet ID")
    bet9ja_key: str | None = Field(default=None, max_length=50, description="Bet9ja key")
    outcome_mapping: list[OutcomeMappingSchema] = Field(description="Outcome definitions")
    priority: int = Field(default=0, ge=0, le=100, description="Override priority (0-100)")
    reason: str | None = Field(default=None, max_length=500, description="Audit reason")


class UpdateMappingRequest(BaseModel):
    """Partial update for user mapping.

    Request body for PATCH /api/mappings/{canonical_id}.
    Only provided fields are updated.

    Attributes:
        name: New market name (max 255 chars).
        betpawa_id: New BetPawa marketType.id (max 50 chars).
        sportybet_id: New SportyBet market.id (max 50 chars).
        bet9ja_key: New Bet9ja key prefix (max 50 chars).
        outcome_mapping: New outcome definitions.
        priority: New override priority 0-100.
        is_active: Activate/deactivate mapping.
        reason: Optional reason for audit log.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str | None = Field(default=None, max_length=255, description="Market name")
    betpawa_id: str | None = Field(default=None, max_length=50, description="BetPawa ID")
    sportybet_id: str | None = Field(default=None, max_length=50, description="SportyBet ID")
    bet9ja_key: str | None = Field(default=None, max_length=50, description="Bet9ja key")
    outcome_mapping: list[OutcomeMappingSchema] | None = Field(
        default=None, description="Outcome definitions"
    )
    priority: int | None = Field(default=None, ge=0, le=100, description="Override priority")
    is_active: bool | None = Field(default=None, description="Active status")
    reason: str | None = Field(default=None, max_length=500, description="Audit reason")


class ReloadResponse(BaseModel):
    """Response for cache reload.

    Confirms successful cache reload with statistics.

    Attributes:
        status: Always 'ok' on success.
        mapping_count: Total mappings after reload.
        reloaded_at: When reload completed.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    status: str = Field(description="Status: 'ok'")
    mapping_count: int = Field(description="Total mappings loaded")
    reloaded_at: datetime = Field(description="Reload timestamp")


class PlatformCounts(BaseModel):
    """Platform-specific mapping counts.

    Attributes:
        betpawa_count: Mappings with BetPawa ID.
        sportybet_count: Mappings with SportyBet ID.
        bet9ja_count: Mappings with Bet9ja key.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    betpawa_count: int = Field(description="Mappings with BetPawa ID")
    sportybet_count: int = Field(description="Mappings with SportyBet ID")
    bet9ja_count: int = Field(description="Mappings with Bet9ja key")


class UnmappedCounts(BaseModel):
    """Unmapped market status counts.

    Attributes:
        new: Markets with NEW status.
        acknowledged: Markets with ACKNOWLEDGED status.
        mapped: Markets with MAPPED status.
        ignored: Markets with IGNORED status.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    new: int = Field(description="NEW status count")
    acknowledged: int = Field(description="ACKNOWLEDGED status count")
    mapped: int = Field(description="MAPPED status count")
    ignored: int = Field(description="IGNORED status count")


class MappingStatsResponse(BaseModel):
    """Mapping dashboard statistics.

    Aggregated statistics from mapping cache and unmapped market log.

    Attributes:
        total_mappings: Total mappings in cache.
        code_mappings: Mappings from code.
        db_mappings: Mappings from database.
        by_platform: Platform-specific mapping counts.
        unmapped_counts: Unmapped market status breakdown.
        cache_loaded_at: When cache was last loaded.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    total_mappings: int = Field(description="Total mappings in cache")
    code_mappings: int = Field(description="Code-defined mappings")
    db_mappings: int = Field(description="Database mappings")
    by_platform: PlatformCounts = Field(description="Platform counts")
    unmapped_counts: UnmappedCounts = Field(description="Unmapped status breakdown")
    cache_loaded_at: datetime | None = Field(description="Cache load timestamp")
