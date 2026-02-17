"""Storage sample model for historical size tracking.

This module defines the StorageSample model for tracking database size
over time. Samples are recorded daily by a scheduled job and retained
for 90 days to enable trend analysis.
"""

from datetime import datetime

from sqlalchemy import BigInteger, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class StorageSample(Base):
    """Tracks database storage size over time for trend analysis.

    Records periodic snapshots of database size including total size
    and per-table breakdown. Used by monitoring dashboards to visualize
    storage growth trends.

    Attributes:
        id: Primary key.
        sampled_at: When the sample was taken.
        total_bytes: Total database size in bytes.
        table_sizes: JSON dict mapping table name to size in bytes.
    """

    __tablename__ = "storage_samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    sampled_at: Mapped[datetime] = mapped_column(server_default=func.now())
    total_bytes: Mapped[int] = mapped_column(BigInteger)
    table_sizes: Mapped[dict] = mapped_column(JSON)
