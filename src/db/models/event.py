"""Event and EventBookmaker models.

This module defines the core Event model representing matched sporting
events and the EventBookmaker junction table linking events to bookmaker-
specific data like external IDs and URLs.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.bookmaker import Bookmaker
    from src.db.models.sport import Tournament


class Event(Base):
    """Matched event across betting platforms.

    Represents a sporting event that has been matched across multiple
    bookmakers using SportRadar ID. The Event table stores canonical
    event data from Betpawa (the reference platform).

    Attributes:
        id: Primary key.
        tournament_id: FK to tournaments table.
        name: Display name (e.g., "Arsenal vs Chelsea").
        home_team: Home team name.
        away_team: Away team name.
        kickoff: Event start time (UTC).
        sportradar_id: Cross-platform matching key (unique).
        created_at: Timestamp when record was created.

    Relationships:
        tournament: Parent Tournament (many-to-one).
        bookmaker_links: EventBookmaker entries (one-to-many, cascade delete).

    Constraints:
        - sportradar_id: unique
    """

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
    """Per-bookmaker event data linking an event to bookmaker-specific info.

    Junction table connecting events to bookmakers with platform-specific
    identifiers. Used to map canonical events to bookmaker event pages.

    Attributes:
        id: Primary key.
        event_id: FK to events table.
        bookmaker_id: FK to bookmakers table.
        external_event_id: Bookmaker's internal event ID.
        event_url: Direct URL to event page on bookmaker site.
        created_at: Timestamp when record was created.

    Relationships:
        event: Parent Event (many-to-one).
        bookmaker: Associated Bookmaker (many-to-one).

    Constraints:
        - Unique on (event_id, bookmaker_id): One link per event-bookmaker pair.
    """

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
