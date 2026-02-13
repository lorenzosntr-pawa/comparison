"""Market mapping models for user-defined mappings and discovery.

This module defines models for the market mapping utility (Phase 101):
- UserMarketMapping: User-defined market mappings with platform IDs
- MappingAuditLog: Audit trail for mapping changes
- UnmappedMarketLog: Discovery log for unmapped markets

These tables support the runtime merge strategy where user mappings
can override or extend code-defined market mappings.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    pass


class UserMarketMapping(Base):
    """User-defined market mapping with platform-specific IDs.

    Stores user-created or user-edited market mappings that can override
    or extend the code-defined MARKET_MAPPINGS. These are loaded at runtime
    and merged with code mappings, with database mappings taking priority.

    Attributes:
        id: Primary key.
        canonical_id: Unique market identifier (e.g., "1x2_ft", "user_over_3.5").
        name: Human-readable name (e.g., "1X2 - Full Time").
        betpawa_id: BetPawa marketType.id, nullable if not mapped.
        sportybet_id: SportyBet market.id, nullable if not mapped.
        bet9ja_key: Bet9ja key prefix (e.g., "S_1X2"), nullable.
        outcome_mapping: JSONB array of outcome mappings.
        priority: Override priority (higher wins over code).
        is_active: Soft delete flag, defaults to true.
        created_at: Creation timestamp.
        updated_at: Last modification timestamp.
        created_by: User identifier (future auth integration).

    Relationships:
        audit_logs: MappingAuditLog entries for this mapping.
    """

    __tablename__ = "user_market_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    betpawa_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sportybet_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bet9ja_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    outcome_mapping: Mapped[list] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    audit_logs: Mapped[list["MappingAuditLog"]] = relationship(
        back_populates="mapping", cascade="all, delete-orphan"
    )


class MappingAuditLog(Base):
    """Audit trail for market mapping changes.

    Tracks all changes to user mappings for accountability and debugging.
    The canonical_id is preserved even if the mapping is deleted to maintain
    audit history.

    Attributes:
        id: Primary key.
        mapping_id: FK to user_market_mappings (SET NULL on delete).
        canonical_id: Mapping canonical_id (preserved even if FK deleted).
        action: One of: CREATE, UPDATE, DELETE, ACTIVATE, DEACTIVATE.
        old_value: Previous state (null for CREATE).
        new_value: New state (null for DELETE).
        reason: Optional explanation for the change.
        created_at: When action occurred.
        created_by: User who made the change.

    Relationships:
        mapping: Parent UserMarketMapping (nullable due to SET NULL).
    """

    __tablename__ = "mapping_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mapping_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("user_market_mappings.id", ondelete="SET NULL"),
        nullable=True,
    )
    canonical_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    old_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    mapping: Mapped[Optional["UserMarketMapping"]] = relationship(
        back_populates="audit_logs"
    )

    __table_args__ = (
        Index("idx_audit_log_mapping", "mapping_id"),
        Index("idx_audit_log_canonical", "canonical_id"),
        Index("idx_audit_log_action", "action"),
        Index("idx_audit_log_created", "created_at"),
    )


class UnmappedMarketLog(Base):
    """Discovery log for unmapped markets.

    Persists unmapped markets discovered during scraping for analysis.
    Used to identify markets that need mapping definitions and track
    their frequency across scrape runs.

    Attributes:
        id: Primary key.
        source: Platform: "sportybet" or "bet9ja".
        external_market_id: Platform's market ID.
        market_name: Market name from platform (if available).
        sample_outcomes: Example outcome structure for reference.
        first_seen_at: When first encountered.
        last_seen_at: When last encountered.
        occurrence_count: How many times seen (for prioritization).
        status: NEW, ACKNOWLEDGED, MAPPED, IGNORED.
        notes: Admin notes about the market.

    Constraints:
        Unique on (source, external_market_id) to prevent duplicates.
    """

    __tablename__ = "unmapped_market_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    external_market_id: Mapped[str] = mapped_column(String(100), nullable=False)
    market_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sample_outcomes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="NEW")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "external_market_id", name="uq_unmapped_source_market"),
        Index("idx_unmapped_source", "source"),
        Index("idx_unmapped_status", "status"),
    )
