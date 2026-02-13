"""Pydantic schemas for unmapped market discovery API.

This module defines schemas for the unmapped markets management API:
- UnmappedMarketListItem: Summary item for paginated listing
- UnmappedMarketListResponse: Paginated list response
- UnmappedMarketDetailResponse: Full unmapped market details
- UpdateUnmappedRequest: Update status and notes

Uses camelCase aliases for frontend compatibility.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class UnmappedMarketListItem(BaseModel):
    """Summary item for unmapped market list.

    Contains essential fields for list display without sample outcomes.

    Attributes:
        id: Database primary key.
        source: Platform identifier ("sportybet" or "bet9ja").
        external_market_id: Platform's market ID.
        market_name: Market name from platform (if available).
        first_seen_at: When first encountered.
        last_seen_at: When last encountered.
        occurrence_count: How many times seen (for prioritization).
        status: NEW, ACKNOWLEDGED, MAPPED, IGNORED.
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int = Field(description="Database primary key")
    source: str = Field(description="Platform: 'sportybet' or 'bet9ja'")
    external_market_id: str = Field(description="Platform's market ID")
    market_name: Optional[str] = Field(default=None, description="Market name from platform")
    first_seen_at: datetime = Field(description="When first encountered")
    last_seen_at: datetime = Field(description="When last encountered")
    occurrence_count: int = Field(description="Number of times seen")
    status: str = Field(description="Status: NEW, ACKNOWLEDGED, MAPPED, IGNORED")


class UnmappedMarketListResponse(BaseModel):
    """Paginated list of unmapped markets.

    Standard pagination response with items and metadata.

    Attributes:
        items: List of unmapped market summaries.
        total: Total count before pagination.
        page: Current page number (1-indexed).
        page_size: Items per page.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    items: list[UnmappedMarketListItem] = Field(description="Unmapped market summaries")
    total: int = Field(description="Total count before pagination")
    page: int = Field(description="Current page (1-indexed)")
    page_size: int = Field(description="Items per page")


class UnmappedMarketDetailResponse(BaseModel):
    """Full unmapped market details.

    Complete unmapped market information including sample outcomes.

    Attributes:
        id: Database primary key.
        source: Platform identifier ("sportybet" or "bet9ja").
        external_market_id: Platform's market ID.
        market_name: Market name from platform (if available).
        sample_outcomes: Example outcome structure for reference.
        first_seen_at: When first encountered.
        last_seen_at: When last encountered.
        occurrence_count: How many times seen (for prioritization).
        status: NEW, ACKNOWLEDGED, MAPPED, IGNORED.
        notes: Admin notes about the market.
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int = Field(description="Database primary key")
    source: str = Field(description="Platform: 'sportybet' or 'bet9ja'")
    external_market_id: str = Field(description="Platform's market ID")
    market_name: Optional[str] = Field(default=None, description="Market name from platform")
    sample_outcomes: Optional[list[dict]] = Field(
        default=None, description="Example outcomes for reference"
    )
    first_seen_at: datetime = Field(description="When first encountered")
    last_seen_at: datetime = Field(description="When last encountered")
    occurrence_count: int = Field(description="Number of times seen")
    status: str = Field(description="Status: NEW, ACKNOWLEDGED, MAPPED, IGNORED")
    notes: Optional[str] = Field(default=None, description="Admin notes")


class UpdateUnmappedRequest(BaseModel):
    """Update unmapped market status.

    Request body for PATCH /api/unmapped/{id}.
    Only provided fields are updated.

    Attributes:
        status: New status (must be one of valid values).
        notes: Admin notes (max 1000 chars).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    status: Optional[str] = Field(
        default=None,
        pattern="^(NEW|ACKNOWLEDGED|MAPPED|IGNORED)$",
        description="Status: NEW, ACKNOWLEDGED, MAPPED, IGNORED",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Admin notes (max 1000 chars)",
    )
