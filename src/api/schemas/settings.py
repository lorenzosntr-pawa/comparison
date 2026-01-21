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
