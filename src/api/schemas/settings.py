"""Pydantic schemas for settings API endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SettingsResponse(BaseModel):
    """Response model for settings endpoint."""

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    scrape_interval_minutes: int
    enabled_platforms: list[str]
    odds_retention_days: int
    match_retention_days: int
    cleanup_frequency_hours: int

    # Scraping tuning parameters (Phase 40)
    betpawa_concurrency: int
    sportybet_concurrency: int
    bet9ja_concurrency: int
    bet9ja_delay_ms: int
    batch_size: int

    updated_at: datetime | None


class SettingsUpdate(BaseModel):
    """Request model for updating settings."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    scrape_interval_minutes: int | None = Field(
        default=None, ge=1, le=60, description="Scrape interval in minutes (1-60)"
    )
    enabled_platforms: list[str] | None = Field(
        default=None, description="List of platform slugs to enable"
    )
    odds_retention_days: int | None = Field(
        default=None, ge=1, le=365, description="Days to keep odds snapshots (1-365)"
    )
    match_retention_days: int | None = Field(
        default=None, ge=1, le=365, description="Days to keep matches by kickoff (1-365)"
    )
    cleanup_frequency_hours: int | None = Field(
        default=None, ge=1, le=168, description="Hours between cleanup runs (1-168)"
    )

    # Scraping tuning parameters (Phase 40)
    betpawa_concurrency: int | None = Field(
        default=None, ge=1, le=100, description="BetPawa concurrent requests (1-100)"
    )
    sportybet_concurrency: int | None = Field(
        default=None, ge=1, le=100, description="SportyBet concurrent requests (1-100)"
    )
    bet9ja_concurrency: int | None = Field(
        default=None, ge=1, le=50, description="Bet9ja concurrent requests (1-50)"
    )
    bet9ja_delay_ms: int | None = Field(
        default=None, ge=0, le=100, description="Bet9ja delay between requests in ms (0-100)"
    )
    batch_size: int | None = Field(
        default=None, ge=10, le=200, description="Events per batch (10-200)"
    )
