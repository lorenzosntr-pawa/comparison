"""Database models package."""

from src.db.base import Base
from src.db.models.bookmaker import Bookmaker
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
    CompetitorSource,
    CompetitorTournament,
)
from src.db.models.event import Event, EventBookmaker
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.db.models.scrape import ScrapeError, ScrapePhaseLog, ScrapeRun, ScrapeStatus
from src.db.models.settings import Settings
from src.db.models.sport import Sport, Tournament

__all__ = [
    "Base",
    "Sport",
    "Tournament",
    "Bookmaker",
    "Event",
    "EventBookmaker",
    "OddsSnapshot",
    "MarketOdds",
    "ScrapeRun",
    "ScrapeError",
    "ScrapePhaseLog",
    "ScrapeStatus",
    "Settings",
    # Competitor models
    "CompetitorSource",
    "CompetitorTournament",
    "CompetitorEvent",
    "CompetitorOddsSnapshot",
    "CompetitorMarketOdds",
]
