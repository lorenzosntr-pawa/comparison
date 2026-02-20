"""Pydantic schemas for settings API endpoints.

This module defines schemas for the application settings system:
- SettingsResponse: Current configuration values
- SettingsUpdate: Partial update request

Settings control scraping behavior, data retention, and concurrency tuning.
Uses camelCase aliases for frontend compatibility.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SettingsResponse(BaseModel):
    """Response model for settings endpoint.

    Contains all configurable settings for the application including
    scrape intervals, retention policies, concurrency tuning, and alert configuration.

    Attributes:
        scrape_interval_minutes: Minutes between scheduled scrapes.
        enabled_platforms: List of enabled platform slugs.
        odds_retention_days: Days to keep odds snapshots.
        match_retention_days: Days to keep match data.
        cleanup_frequency_hours: Hours between cleanup runs.
        betpawa_concurrency: BetPawa concurrent request limit.
        sportybet_concurrency: SportyBet concurrent request limit.
        bet9ja_concurrency: Bet9ja concurrent request limit.
        bet9ja_delay_ms: Delay between Bet9ja requests (rate limiting).
        batch_size: Events per scrape batch.
        max_concurrent_events: Max concurrent events within a batch.
        alert_enabled: Master toggle for alert detection.
        alert_threshold_warning: % change threshold for WARNING severity.
        alert_threshold_elevated: % change threshold for ELEVATED severity.
        alert_threshold_critical: % change threshold for CRITICAL severity.
        alert_retention_days: Days to keep alerts.
        alert_lookback_minutes: Comparison window for direction disagreement.
        updated_at: When settings were last modified.
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    scrape_interval_minutes: int = Field(description="Minutes between scheduled scrapes")
    enabled_platforms: list[str] = Field(description="Enabled platform slugs")
    odds_retention_days: int = Field(description="Days to keep odds snapshots")
    match_retention_days: int = Field(description="Days to keep match data")
    cleanup_frequency_hours: int = Field(description="Hours between cleanup runs")

    # Scraping tuning parameters (Phase 40)
    betpawa_concurrency: int = Field(description="BetPawa concurrent requests")
    sportybet_concurrency: int = Field(description="SportyBet concurrent requests")
    bet9ja_concurrency: int = Field(description="Bet9ja concurrent requests")
    bet9ja_delay_ms: int = Field(description="Bet9ja request delay in ms")
    batch_size: int = Field(description="Events per scrape batch")

    # Intra-batch event concurrency (Phase 56)
    max_concurrent_events: int = Field(description="Max concurrent events per batch")

    # Alert configuration (Phase 111)
    alert_enabled: bool = Field(description="Master toggle for alert detection")
    alert_threshold_warning: float = Field(description="% change threshold for WARNING severity")
    alert_threshold_elevated: float = Field(description="% change threshold for ELEVATED severity")
    alert_threshold_critical: float = Field(description="% change threshold for CRITICAL severity")
    alert_retention_days: int = Field(description="Days to keep alerts")
    alert_lookback_minutes: int = Field(description="Comparison window for direction disagreement")

    updated_at: datetime | None = Field(description="Last modification time")


class SettingsUpdate(BaseModel):
    """Request model for updating settings.

    Supports partial updates - only provided fields are updated.
    All fields are optional with validation constraints.

    Attributes:
        scrape_interval_minutes: Minutes between scheduled scrapes (1-60).
        enabled_platforms: Platform slugs to enable.
        odds_retention_days: Days to keep odds snapshots (1-365).
        match_retention_days: Days to keep matches (1-365).
        cleanup_frequency_hours: Hours between cleanup runs (1-168).
        betpawa_concurrency: BetPawa concurrent requests (1-100).
        sportybet_concurrency: SportyBet concurrent requests (1-100).
        bet9ja_concurrency: Bet9ja concurrent requests (1-50).
        bet9ja_delay_ms: Bet9ja request delay in ms (0-100).
        batch_size: Events per batch (10-200).
        max_concurrent_events: Max concurrent events per batch (1-50).
        alert_enabled: Master toggle for alert detection.
        alert_threshold_warning: % change threshold for WARNING severity (1-50).
        alert_threshold_elevated: % change threshold for ELEVATED severity (1-50).
        alert_threshold_critical: % change threshold for CRITICAL severity (1-100).
        alert_retention_days: Days to keep alerts (1-90).
        alert_lookback_minutes: Comparison window in minutes (15-180).
    """

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

    # Intra-batch event concurrency (Phase 56)
    max_concurrent_events: int | None = Field(
        default=None, ge=1, le=50, description="Max concurrent events per batch (1-50)"
    )

    # Alert configuration (Phase 111)
    alert_enabled: bool | None = Field(
        default=None, description="Master toggle for alert detection"
    )
    alert_threshold_warning: float | None = Field(
        default=None, ge=1.0, le=50.0, description="% change for WARNING severity (1-50)"
    )
    alert_threshold_elevated: float | None = Field(
        default=None, ge=1.0, le=50.0, description="% change for ELEVATED severity (1-50)"
    )
    alert_threshold_critical: float | None = Field(
        default=None, ge=1.0, le=100.0, description="% change for CRITICAL severity (1-100)"
    )
    alert_retention_days: int | None = Field(
        default=None, ge=1, le=90, description="Days to keep alerts (1-90)"
    )
    alert_lookback_minutes: int | None = Field(
        default=None, ge=15, le=180, description="Comparison window in minutes (15-180)"
    )
