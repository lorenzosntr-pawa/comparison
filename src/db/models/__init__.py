"""Database models package."""

from src.db.base import Base
from src.db.models.bookmaker import Bookmaker
from src.db.models.cleanup_run import CleanupRun
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
    CompetitorSource,
    CompetitorTournament,
)
from src.db.models.event import Event, EventBookmaker
from src.db.models.event_scrape_status import EventScrapeStatus
from src.db.models.market_odds import MarketOddsCurrent, MarketOddsHistory
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.db.models.scrape import (
    ScrapeBatch,
    ScrapeError,
    ScrapePhaseLog,
    ScrapeRun,
    ScrapeStatus,
)
from src.db.models.settings import Settings
from src.db.models.sport import Sport, Tournament
from src.db.models.storage_alert import StorageAlert
from src.db.models.storage_sample import StorageSample

__all__ = [
    "Base",
    "Sport",
    "Tournament",
    "Bookmaker",
    "Event",
    "EventBookmaker",
    "OddsSnapshot",
    "MarketOdds",
    # Market-level storage (Phase 106)
    "MarketOddsCurrent",
    "MarketOddsHistory",
    "ScrapeBatch",
    "ScrapeRun",
    "ScrapeError",
    "ScrapePhaseLog",
    "ScrapeStatus",
    "Settings",
    "CleanupRun",
    # Competitor models
    "CompetitorSource",
    "CompetitorTournament",
    "CompetitorEvent",
    "CompetitorOddsSnapshot",
    "CompetitorMarketOdds",
    # Event-centric architecture models
    "EventScrapeStatus",
    # Storage monitoring
    "StorageSample",
    "StorageAlert",
]
