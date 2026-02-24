"""Settings API endpoints for scraping configuration."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.settings import SettingsResponse, SettingsUpdate
from src.db.engine import get_db
from src.db.models.settings import Settings
from src.scheduling.scheduler import update_scheduler_interval

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_or_create_settings(db: AsyncSession) -> Settings:
    """Get settings from database, creating default if not exists.

    Args:
        db: Database session.

    Returns:
        Settings object with id=1.
    """
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings = result.scalar_one_or_none()

    if settings is None:
        # Create default settings if not exists
        settings = Settings(
            id=1,
            scrape_interval_minutes=5,
            enabled_platforms=["sportybet", "betpawa", "bet9ja"],
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """Get current scraping settings.

    Returns all configurable settings including scrape interval, enabled
    platforms, retention settings, and concurrency tuning parameters.

    Args:
        db: Async database session (injected).

    Returns:
        SettingsResponse with all current configuration values.
    """
    settings = await get_or_create_settings(db)
    return SettingsResponse.model_validate(settings)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    update: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """Update scraping settings.

    Partial update - only provided fields will be updated. Changes to
    scrape_interval_minutes take effect immediately by updating the
    scheduler at runtime.

    Args:
        update: Settings fields to update (only non-null fields applied).
        db: Async database session (injected).

    Returns:
        SettingsResponse with all settings after the update.

    Note:
        Invalid platform slugs in enabled_platforms are silently filtered out.
    """
    settings = await get_or_create_settings(db)

    # Update only provided fields
    if update.scrape_interval_minutes is not None:
        settings.scrape_interval_minutes = update.scrape_interval_minutes
        # Update scheduler interval at runtime
        update_scheduler_interval(update.scrape_interval_minutes)

    if update.enabled_platforms is not None:
        # Validate platform slugs
        valid_platforms = {"sportybet", "betpawa", "bet9ja"}
        settings.enabled_platforms = [
            p for p in update.enabled_platforms if p in valid_platforms
        ]

    if update.odds_retention_days is not None:
        settings.odds_retention_days = update.odds_retention_days

    if update.match_retention_days is not None:
        settings.match_retention_days = update.match_retention_days

    if update.cleanup_frequency_hours is not None:
        settings.cleanup_frequency_hours = update.cleanup_frequency_hours

    # Scraping concurrency tuning parameters (Phase 40 + Phase 56)
    if update.betpawa_concurrency is not None:
        settings.betpawa_concurrency = update.betpawa_concurrency

    if update.sportybet_concurrency is not None:
        settings.sportybet_concurrency = update.sportybet_concurrency

    if update.bet9ja_concurrency is not None:
        settings.bet9ja_concurrency = update.bet9ja_concurrency

    if update.bet9ja_delay_ms is not None:
        settings.bet9ja_delay_ms = update.bet9ja_delay_ms

    if update.batch_size is not None:
        settings.batch_size = update.batch_size

    if update.max_concurrent_events is not None:
        settings.max_concurrent_events = update.max_concurrent_events

    # Alert configuration (Phase 111)
    if update.alert_enabled is not None:
        settings.alert_enabled = update.alert_enabled

    if update.alert_threshold_warning is not None:
        settings.alert_threshold_warning = update.alert_threshold_warning

    if update.alert_threshold_elevated is not None:
        settings.alert_threshold_elevated = update.alert_threshold_elevated

    if update.alert_threshold_critical is not None:
        settings.alert_threshold_critical = update.alert_threshold_critical

    if update.alert_retention_days is not None:
        settings.alert_retention_days = update.alert_retention_days

    if update.alert_lookback_minutes is not None:
        settings.alert_lookback_minutes = update.alert_lookback_minutes

    await db.commit()
    await db.refresh(settings)

    return SettingsResponse.model_validate(settings)
