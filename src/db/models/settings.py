"""Settings model for scraping configuration.

This module defines the Settings model for storing application-wide
configuration including scrape intervals, enabled platforms, retention
policies, and per-platform concurrency tuning.
"""

from datetime import datetime

from sqlalchemy import JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Settings(Base):
    """Singleton settings for scraping configuration.

    Uses a single-row pattern with id=1 for all application settings.
    Queried at startup and cached, with updates triggering cache refresh.

    Attributes:
        id: Primary key (always 1 for singleton pattern).
        scrape_interval_minutes: Time between scheduled scrapes.
        enabled_platforms: JSON list of active platform slugs.
            Example: ["sportybet", "betpawa", "bet9ja"]
        odds_retention_days: Days to keep odds snapshots before cleanup.
        match_retention_days: Days to keep match data before cleanup.
        cleanup_frequency_hours: Hours between cleanup job runs.
        betpawa_concurrency: Max concurrent requests to Betpawa.
        sportybet_concurrency: Max concurrent requests to SportyBet.
        bet9ja_concurrency: Max concurrent requests to Bet9ja.
        bet9ja_delay_ms: Delay between Bet9ja requests (rate limiting).
        batch_size: Number of events to process per batch.
        max_concurrent_events: Max events to scrape concurrently.
        created_at: Timestamp when settings were initialized.
        updated_at: Timestamp of last modification.
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

    # Scraping tuning parameters (Phase 40)
    betpawa_concurrency: Mapped[int] = mapped_column(default=50)
    sportybet_concurrency: Mapped[int] = mapped_column(default=50)
    bet9ja_concurrency: Mapped[int] = mapped_column(default=15)
    bet9ja_delay_ms: Mapped[int] = mapped_column(default=25)
    batch_size: Mapped[int] = mapped_column(default=50)

    # Intra-batch event concurrency (Phase 56)
    max_concurrent_events: Mapped[int] = mapped_column(default=10)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=func.now(), nullable=True
    )
