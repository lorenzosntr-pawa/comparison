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

    Returns:
        Current settings including interval and enabled platforms.
    """
    settings = await get_or_create_settings(db)
    return SettingsResponse.model_validate(settings)


@router.put("", response_model=SettingsResponse)
async def update_settings(
    update: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> SettingsResponse:
    """Update scraping settings.

    Partial update - only provided fields will be updated.

    Args:
        update: Settings fields to update.
        db: Database session.

    Returns:
        Updated settings.
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

    await db.commit()
    await db.refresh(settings)

    return SettingsResponse.model_validate(settings)
