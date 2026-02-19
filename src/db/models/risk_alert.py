"""Risk alert model for odds movement detection.

This module defines the RiskAlert model for storing detected risk events
including significant price changes, direction disagreements between
bookmakers, and market availability changes.

Alerts support acknowledgment workflow and automatic status transitions
after event kickoff.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.event import Event


class AlertStatus(str, Enum):
    """Workflow status for risk alerts."""

    NEW = "new"  # Unacknowledged, pre-kickoff
    ACKNOWLEDGED = "acknowledged"  # User reviewed, pre-kickoff
    PAST = "past"  # Post-kickoff (automatic transition)


class RiskAlert(Base):
    """Detected risk event requiring monitoring attention.

    Records significant odds movements, direction disagreements between
    bookmakers, and market availability changes. Supports acknowledgment
    workflow and automatic post-kickoff status transitions.

    Attributes:
        id: Primary key (BigInteger for high volume).
        event_id: FK to events table.
        bookmaker_slug: Which bookmaker triggered the alert.
        market_id: Betpawa market ID affected.
        market_name: Human-readable market name.
        line: Line value for total/handicap markets (nullable).
        outcome_name: Specific outcome if applicable (nullable).
        alert_type: Type of alert (price_change, direction_disagreement, availability).
        severity: Severity level (warning, elevated, critical).
        change_percent: Absolute percentage change (0 for availability).
        old_value: Previous odds value (nullable for availability).
        new_value: Current odds value (nullable for availability).
        competitor_direction: For disagreement: "sportybet:up" format (nullable).
        detected_at: When the alert was detected.
        acknowledged_at: When user acknowledged (nullable).
        status: Current workflow status (new, acknowledged, past).
        event_kickoff: Kickoff time for automatic PAST transition.

    Relationships:
        event: Parent Event (many-to-one).

    Indexes:
        - idx_risk_alerts_event: (event_id, status) for event page badge queries
        - idx_risk_alerts_status_detected: (status, detected_at DESC) for Risk Monitoring page
        - idx_risk_alerts_kickoff: (event_kickoff) for auto-status background job
    """

    __tablename__ = "risk_alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    bookmaker_slug: Mapped[str] = mapped_column(String(50))
    market_id: Mapped[str] = mapped_column(String(50))
    market_name: Mapped[str] = mapped_column(String(255))
    line: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50))  # AlertType enum value
    severity: Mapped[str] = mapped_column(String(20))  # AlertSeverity enum value
    change_percent: Mapped[float] = mapped_column(Float, default=0.0)
    old_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    competitor_direction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="new")  # AlertStatus enum value
    event_kickoff: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    event: Mapped["Event"] = relationship()

    __table_args__ = (
        # For event page badge queries: "count alerts for this event"
        Index("idx_risk_alerts_event", "event_id", "status"),
        # For Risk Monitoring page: "all NEW alerts, most recent first"
        Index(
            "idx_risk_alerts_status_detected",
            "status",
            "detected_at",
        ),
        # For auto-status job: "find alerts past kickoff"
        Index("idx_risk_alerts_kickoff", "event_kickoff"),
    )
