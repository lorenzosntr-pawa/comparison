"""Event and EventBookmaker models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.bookmaker import Bookmaker
    from src.db.models.sport import Tournament


class Event(Base):
    """Matched event across platforms."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"))
    name: Mapped[str] = mapped_column(String(500))
    home_team: Mapped[str] = mapped_column(String(255))
    away_team: Mapped[str] = mapped_column(String(255))
    kickoff: Mapped[datetime] = mapped_column()
    sportradar_id: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    tournament: Mapped["Tournament"] = relationship(back_populates="events")
    bookmaker_links: Mapped[list["EventBookmaker"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventBookmaker(Base):
    """Per-bookmaker event data (links event to bookmaker-specific info)."""

    __tablename__ = "event_bookmakers"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    bookmaker_id: Mapped[int] = mapped_column(ForeignKey("bookmakers.id"))
    external_event_id: Mapped[str] = mapped_column(String(100))
    event_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="bookmaker_links")
    bookmaker: Mapped["Bookmaker"] = relationship()

    __table_args__ = (
        UniqueConstraint("event_id", "bookmaker_id", name="uq_event_bookmaker"),
    )
