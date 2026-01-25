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
