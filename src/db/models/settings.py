"""Settings model for scraping configuration."""

from datetime import datetime

from sqlalchemy import JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Settings(Base):
    """Singleton settings for scraping configuration.

    Uses a single-row pattern with id=1 for all settings.
    Settings include scheduler interval, enabled platforms, and retention policies.
    """

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_interval_minutes: Mapped[int] = mapped_column(default=5)
    enabled_platforms: Mapped[list[str]] = mapped_column(
        JSON, default=["sportybet", "betpawa", "bet9ja"]
    )
    odds_retention_days: Mapped[int] = mapped_column(default=30)
    match_retention_days: Mapped[int] = mapped_column(default=30)
    cleanup_frequency_hours: Mapped[int] = mapped_column(default=24)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=func.now(), nullable=True
    )
