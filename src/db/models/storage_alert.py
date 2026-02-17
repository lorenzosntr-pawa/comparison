"""Storage alert model for abnormal growth detection.

This module defines the StorageAlert model for tracking database
growth warnings and critical size alerts. Alerts are created by
the storage sampling job when thresholds are exceeded.
"""

from datetime import datetime

from sqlalchemy import BigInteger, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class StorageAlert(Base):
    """Tracks storage alerts for abnormal database growth.

    Alerts are created by sample_storage_sizes() when growth rate exceeds
    thresholds or total size reaches critical levels. Operators can
    dismiss alerts to mark them as resolved.

    Attributes:
        id: Primary key.
        created_at: When the alert was created.
        alert_type: Type of alert ('growth_warning' or 'size_critical').
        message: Human-readable description of the alert.
        current_bytes: Database size when alert was created.
        previous_bytes: Previous sample size (for growth calculation).
        growth_percent: Growth percentage from previous sample.
        resolved_at: When alert was dismissed (None if active).
    """

    __tablename__ = "storage_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    alert_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(500))
    current_bytes: Mapped[int] = mapped_column(BigInteger)
    previous_bytes: Mapped[int] = mapped_column(BigInteger)
    growth_percent: Mapped[float] = mapped_column(Float)
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)
